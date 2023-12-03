from typing import Optional
from django.db.models.base import ModelBase
from server.settings import MODELS_FIELDS_NAMES_MAP, FIELDS_TO_DATE_FORMAT, FIELDS_BOOLEAN_TYPE
from converters.time_converter import TimeConverter


class NamesConverter(TimeConverter):

    @staticmethod
    def _get_dict_key_by_value(dictionary: dict, value: str) -> str:
        return list(dictionary.keys())[list(dictionary.values()).index(value)]

    @staticmethod
    def _get_nested_filed_from_dict(
            dictionary: dict,
            key: str,
            nested_key: str,
    ) -> Optional[str]:
        if dictionary.get(key):
            return dictionary[key].get(nested_key)

    def many_from_db_to_airtable(self, records: list[ModelBase], table_name: str) -> list:
        airtable_records = list()
        for record in records:
            airtable_records.append(
                self.record_from_database_to_airtable(
                    record=record.__dict__,
                    table_name=table_name
                )
            )
        return airtable_records

    @staticmethod
    def record_from_database_to_airtable(record: dict, table_name: str) -> dict:
        exclude_fields = MODELS_FIELDS_NAMES_MAP[table_name]['exclude_database_fields']
        for field in exclude_fields:
            try:
                record.pop(field)
            except KeyError:
                pass
        airtable_record = dict()
        for key in record:
            if key in MODELS_FIELDS_NAMES_MAP[table_name]["fields"]:
                if key == "id":
                    airtable_record["ID"] = str(record["id"])
                else:
                    airtable_record[MODELS_FIELDS_NAMES_MAP[table_name]["fields"][key]] = record[key]
        return airtable_record

    def convert_records_to_database_format(self, records: list, db_fields: list, table_name: str) -> list:
        database_records = []
        fields_map = MODELS_FIELDS_NAMES_MAP[table_name]['fields']
        for record in records:
            fields = record['fields']
            database_record = dict()
            database_record['air_id'] = record['id']
            for db_field in db_fields:
                if not db_field == "air_id":
                    database_record[db_field] = self._validate_field(
                        field_name=fields_map[db_field],
                        field_value=fields.get(fields_map[db_field])
                    )
            database_records.append(database_record)
        return database_records

    def _validate_field(self, field_name: str, field_value: any) -> any:
        if isinstance(field_value, dict):
            return field_value['name']
        elif field_name == "ID":
            return int(field_value)
        elif field_name in FIELDS_TO_DATE_FORMAT:
            self.str_datetime_to_datetime(str_datetime=field_value)
        elif field_name in FIELDS_BOOLEAN_TYPE:
            return False if not field_value else field_value
        return field_value
