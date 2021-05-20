rm(list=ls())
# ============================================================================================================
library(ggplot2)
library(scales)
# ============================================================================================================

# ============================================================================================================
read_exploration_report <- function(file_path) {
  # ============================================================================================================
  report <- read.table(file=file_path, 
                       header = FALSE, 
                       sep = ",",
                       blank.lines.skip = TRUE, 
                       fill = TRUE)
  
  # ============================================================================================================
  # manoeuver to put the correct headers
  # https://stackoverflow.com/questions/37302612/column-names-shift-to-left-on-read-table-or-read-csv
  # https://stackoverflow.com/questions/13271820/specifying-row-names-when-reading-in-a-file
  # https://stackoverflow.com/questions/23209330/how-to-change-the-first-row-to-be-the-header-in-r?rq=1
  names(report) <- as.matrix(report[1, ])
  report <- report[-1, ]
  report[] <- lapply(report, function(x) type.convert(as.character(x)))
  report
}
# ============================================================================================================

geom_ptsize = 1
geom_stroke = 1
geom_shape = 19

make_plot_diagram <- function(report_file_str,plot_title_str) {
  report_data <- read_exploration_report(report_file_str)
  retained <- c("1f","1") # 36 , 91
  selected_ids <- report_data[report_data$orig_trace_id %in% retained,]
  
  g <- ggplot(selected_ids,aes(x=trace_len,y=analysis_time, color=as.factor(orig_trace_id))) + 
    geom_point(size = geom_ptsize, stroke = geom_stroke, shape = geom_shape) + 
    scale_colour_discrete(drop=TRUE,
                          limits = levels(as.factor(selected_ids$orig_trace_id))) + 
    labs(colour = "id", x = "trace length", y = "trace analysis time (seconds)") +
    stat_smooth(aes=(color=as.factor(selected_ids$orig_trace_id)), size=1.25, method = "loess", level = 0.95, fullrange = TRUE, se = FALSE) +
    ggtitle(plot_title_str) +
    theme(plot.title = element_text(margin = margin(b = -25)),
          axis.title.x = element_text(margin = margin(t = 5)),
          axis.title.y = element_text(margin = margin(r = 5)))
  
  (g + scale_color_manual(values=c("blue", "red")))
}

make_plot_diagram("mqtt_perf_report.txt", 
                  "Analysis of behavior with multiple loopP instanciations (labelled case)")

make_plot_diagram("mqtt_perf_report_with_data.txt",
                  "Analysis of behavior with multiple loopP instanciations (with value passing)")

