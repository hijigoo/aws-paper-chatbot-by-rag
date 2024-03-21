import os
import boto3
import time
import helpers.image_helper as image_helper
from pdf2image import convert_from_bytes

textract = boto3.client('textract')
s3_client = boto3.client('s3')

doc_prefix = 'doc_input'
figure_prefix = 'figures'


def process_textract(bucket, filename):
    response = textract.start_document_analysis(
        DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': f'{doc_prefix}/{filename}'}},
        FeatureTypes=["LAYOUT"])  ## ["TABLES", "FORMS"]
    return response


def get_layout_blockmap(blocks):
    # get key and value maps
    block_map = {}
    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block

    return block_map


def get_text(result, blocks_map):
    text = ''
    if result is not None and 'Relationships' in result:
        for relationship in result['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    word = blocks_map[child_id]
                    if word['BlockType'] == 'LINE':
                        text += word['Text'] + ' '
    return text


def run_job(filename, bucket):
    jobid = ''
    filename = filename.split('/')[-1]
    try:
        response = process_textract(bucket, filename)
        jobid = response['JobId']
    except Exception as e:
        print("Exception : {}".format(e))
        pass
    finally:
        print(jobid)

    return jobid


def wait_job_to_finish(job_id):
    max_time = time.time() + 3 * 60 * 60  # 3 hours
    while time.time() < max_time:

        response = textract.get_document_analysis(JobId=job_id)
        status = response["JobStatus"]
        print("Analyzing Textract for job {} : {}".format(job_id, status))

        if status == "SUCCEEDED" or status == "FAILED":
            break

        time.sleep(3)


def get_multipages_block_result(job_id):
    maxResults = 1000
    paginationToken = None
    finished = False
    textract = boto3.client('textract')

    doc_block = {}
    init_val = False
    while finished == False:

        #  print("paginationToken : {}".format(paginationToken))
        response = None
        if paginationToken == None:
            print('Analyzed Document Text')
            response = textract.get_document_analysis(JobId=job_id, MaxResults=maxResults)
        else:
            response = textract.get_document_analysis(JobId=job_id,
                                                      MaxResults=maxResults,
                                                      NextToken=paginationToken)

        # Get the text blocks
        blocks = response['Blocks']

        if not init_val:

            print('Pages: {}'.format(response['DocumentMetadata']['Pages']))
            for i in range(int(response['DocumentMetadata']['Pages'])):
                doc_block[i] = []
                init_val = True

        for block in blocks:
            doc_block[int(block['Page']) - 1].append(block)

            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True
    return doc_block


def s3_upload_document(filepath, bucket_name, filename):
    s3_url = f'{doc_prefix}/{filename}'
    s3_client.upload_file(filepath, bucket_name, s3_url)
    return s3_url


def s3_upload_figures(image_path, bucket_name, target_path, filename):
    s3_url = f'{target_path}/{filename}'
    s3_client.upload_file(image_path, bucket_name, s3_url)
    return s3_url


def convert_pdf_to_image(bucket_name, filename):
    try:
        pdf_byte_string = s3_client.get_object(Bucket=bucket_name, Key=f'{doc_prefix}/{filename}')['Body'].read()
        image = convert_from_bytes(pdf_byte_string)
        return image
    except Exception as e:
        print("To show images is s3_upload available only in pdf documents.")
        pass


def extract_images(doc_image, doc_blocks, filename, bucket_name):
    ## 이미지 수와 문서 수가 동일한지 확인
    num_img = len(doc_image)
    num_doc_block = len(doc_blocks)
    if not num_img == num_doc_block:
        assert "The numbers of documents and blocks is different."
    else:
        print("Numbers of documents: {}, and of blocks: {}".format(num_img, num_doc_block))

    s3_urls = []
    s3_file_prefix = filename.replace(".", "_")
    seq = 0
    for page_num, key in enumerate(doc_blocks):
        s3_prefix = f'{figure_prefix}/{s3_file_prefix}/{page_num}'
        local_target_path = f'./figures/{s3_file_prefix}/{page_num}'
        os.makedirs(local_target_path, exist_ok=True)

        for block in doc_blocks[key]:

            if block['BlockType'] == 'LAYOUT_FIGURE':
                crop_image_name = f"{filename}-{seq}.png"
                local_image_path = f"{local_target_path}/{crop_image_name}"
                image_helper.image_crop(doc_image[page_num], block['Geometry']['BoundingBox'], local_image_path)

                s3_url = s3_upload_figures(local_image_path, bucket_name, s3_prefix, crop_image_name)
                s3_urls.append(s3_url)
                print(s3_url)

                seq = seq + 1
    return s3_urls

# job_ids = run_job(filename=test_documents[0], bucket=bucket_name, prefix=doc_bucket_prefix)
# wait_job_to_finish(job_ids=job_ids)
# doc_blocks = get_multipages_block_result(job_id=job_ids[0])
# doc_image = convert_pdf_to_image(bucket_name=bucket_name, bucket_prefix=doc_bucket_prefix, filename=test_documents[0])
# extract_images(doc_image=doc_image, doc_blocks=doc_blocks, filename=test_documents[0], s3_prefix="figures")

# print(doc_block)
