from settings import DSL_FILE_NAME

DSL_TEMPLATE_HEADER = 'parallel ('
DSL_TEMPLATE_BODY = '    {{ build("lamian-runner", partition_id: {}) }},'
DSL_TEMPLATE_FOOTER = ')'


def generate_dsl_file(partition_ids):
    with open(DSL_FILE_NAME, "w") as text_file:
        text_file.write(DSL_TEMPLATE_HEADER + '\n')
        for idx in range(len(partition_ids)):
            text_file.write(DSL_TEMPLATE_BODY.format(partition_ids[idx]) + '\n')
        text_file.write(DSL_TEMPLATE_FOOTER)

if __name__ == '__main__':
    generate_dsl_file([123, 124, 125, 178, 278, 121, 122])