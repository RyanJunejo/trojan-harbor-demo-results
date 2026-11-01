FROM python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea
RUN mkdir -p /grade /tests
COPY grader.py parser_grader.py driver.py expected.json cases_public.json /grade/
RUN chmod 700 /grade && chmod 600 /grade/expected.json /grade/cases_public.json
COPY test.sh /tests/test.sh
RUN chmod 755 /tests/test.sh
