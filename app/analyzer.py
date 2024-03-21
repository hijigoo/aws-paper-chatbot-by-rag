from services import analysis_service

bucket_name = "textract-paper-processor-0410"


# test_documents = ['085310_1_online.pdf']
def upload_document(filepath, filename):
    analysis_service.s3_upload_document(filepath=filepath, bucket_name=bucket_name, filename=filename)


def upload_all_figures(filename):
    job_id = analysis_service.run_job(filename=filename, bucket=bucket_name)
    analysis_service.wait_job_to_finish(job_id=job_id)
    doc_blocks = analysis_service.get_multipages_block_result(job_id=job_id)
    doc_image = analysis_service.convert_pdf_to_image(bucket_name=bucket_name,
                                                      filename=filename)
    s3_urls = analysis_service.extract_images(doc_image=doc_image, doc_blocks=doc_blocks, filename=filename,
                                              bucket_name=bucket_name)
    return s3_urls
