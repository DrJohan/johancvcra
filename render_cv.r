# This script builds both the HTML and PDF versions of your CV

# RStudio normally supplies this path, but Rscript may run outside RStudio.
if (!rmarkdown::pandoc_available() && .Platform$OS.type == "windows") {
  pandoc_dirs <- file.path(
    Sys.getenv("ProgramFiles"), "RStudio",
    c("resources/app/bin/quarto/bin/tools", "bin/quarto/bin/tools", "bin/pandoc")
  )
  pandoc_dirs <- pandoc_dirs[file.exists(file.path(pandoc_dirs, "pandoc.exe"))]
  if (length(pandoc_dirs) > 0) {
    Sys.setenv(RSTUDIO_PANDOC = pandoc_dirs[[1]])
  }
}

if (!rmarkdown::pandoc_available()) {
  stop("Pandoc is required to render the CV. Install Pandoc or render from RStudio.")
}

# If you wanted to speed up rendering for googlesheets driven CVs you could use
# this script to cache a version of the CV_Printer class with data already
# loaded and load the cached version in the .Rmd instead of re-fetching it twice
# for the HTML and PDF rendering. This exercise is left to the reader.

# Knit the HTML version
rmarkdown::render("cv.rmd",
                  params = list(pdf_mode = FALSE),
                  output_file = "index.html")

# Knit the PDF version to temporary html location
dir.create("tmp/pdfs", recursive = TRUE, showWarnings = FALSE)
tmp_html_cv_loc <- file.path("tmp", "pdfs", "cv-pdf.html")
rmarkdown::render("cv.rmd",
                  params = list(pdf_mode = TRUE),
                  output_file = basename(tmp_html_cv_loc),
                  output_dir = dirname(tmp_html_cv_loc))

# Convert to PDF using Pagedown
pagedown::chrome_print(input = tmp_html_cv_loc,
                       output = "drjohan_cv.pdf",
                       wait = 3,
                       timeout = 90,
                       outline = FALSE)

dir.create("output/pdf", recursive = TRUE, showWarnings = FALSE)
if (!file.copy("drjohan_cv.pdf", "output/pdf/drjohan_cv.pdf", overwrite = TRUE)) {
  stop("Could not copy the PDF to output/pdf/drjohan_cv.pdf.")
}
