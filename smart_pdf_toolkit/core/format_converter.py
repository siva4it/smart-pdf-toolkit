from .interfaces import IFormatConverter, OperationResult

class FormatConverter(IFormatConverter):
    def __init__(self):
        pass
    
    def pdf_to_images(self, pdf_path, format, quality):
        return OperationResult(True, "test", [], 0.0, [], [])
    
    def images_to_pdf(self, image_paths, output_path):
        return OperationResult(True, "test", [], 0.0, [], [])
    
    def pdf_to_office(self, pdf_path, target_format):
        return OperationResult(True, "test", [], 0.0, [], [])
    
    def office_to_pdf(self, input_path, output_path):
        return OperationResult(True, "test", [], 0.0, [], [])
    
    def html_to_pdf(self, html_content, output_path):
        return OperationResult(True, "test", [], 0.0, [], [])

