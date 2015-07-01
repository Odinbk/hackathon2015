import psycopg2
import psycopg2.extras


def get_db_dict_connection():
    return psycopg2.connect(
        "dbname='%s' host='%s' port='%s' user='%s'" %
        ('aa_test_management', 'localhost', 5432, 'aa'),
        connection_factory=psycopg2.extras.DictConnection
    )


def get_db_connection():
    return psycopg2.connect(
        "dbname='%s' host='%s' port='%s' user='%s'" %
        ('aa_test_management', 'localhost', 5432, 'aa')
    )


def get_data_from_db(sql_script, args):
    connection = get_db_dict_connection()
    cursor = connection.cursor()
    cursor.execute(sql_script, args)
    col_names = [desc[0] for desc in cursor.description]
    result_list = []
    try:
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            row_dict = dict(zip(col_names, row))
            result_list.append(row_dict)
    finally:
        cursor.close()
        connection.close()

    return result_list


def bulk_write_data_to_db(sql_script, args):
    connection = get_db_dict_connection()
    cursor = connection.cursor()
    try:
        cursor.executemany(sql_script, args)
        connection.commit()
    finally:
        cursor.close()
        connection.close()
