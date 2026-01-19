# ---- Base image with AWS Lambda Runtime for Python 3.12 ----
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.12

# ---- Install Python deps into Lambda task root --------------
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# ---- Copy application code ---------------------------------
COPY health_checker ${LAMBDA_TASK_ROOT}/health_checker

# ---- Set the handler ---------------------------------------
CMD ["health_checker.app.lambda_handler"]