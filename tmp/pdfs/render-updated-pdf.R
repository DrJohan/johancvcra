options(timeout = 90)
Sys.setlocale("LC_CTYPE", ".UTF-8")
Sys.setenv(TZ = "Asia/Kuala_Lumpur")
rmarkdown::render(
  "cv.rmd",
  params = list(pdf_mode = TRUE),
  output_file = "cv-pdf.html",
  output_dir = "tmp/pdfs",
  intermediates_dir = "tmp/pdfs",
  quiet = TRUE,
  envir = new.env(parent = globalenv())
)
pagedown::chrome_print(
  input = "tmp/pdfs/cv-pdf.html",
  output = "output/pdf/drjohan_cv.pdf",
  wait = 3,
  timeout = 90,
  outline = FALSE
)
