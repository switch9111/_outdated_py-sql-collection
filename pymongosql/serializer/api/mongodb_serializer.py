# coding: utf-8
"""
This file contains AbstractSerializer class.
"""
from .abstract_api_serializer import AbstractApiSerializer
from pymongosql.serializer.api.api_serializer_types import (
    Value,
    Column,
    Operator,
    SelectStatement,
    Limit,
    Table,
    Offset,
    Sort
)


class MongodbSerializer(AbstractApiSerializer):
    """
    Defines the MongoDB Api serializer.
    """

    def __init__(self):
        self._OPERATORS = {
            u"$eq": u"=",
            u"$ne": u"!=",
            u"$gt": u">",
            u"$gte": u">=",
            u"$lt": u"<",
            u"$lte": u"<="
        }

    def decode_limit(self, statement, limit):
        statement.limit = Limit(limit)
        return statement


    def decode_sort(self, statement, key_or_list, direction=None):
        if direction is not None:
            statement.sorts = [Sort(key_or_list, direction)]
        else:
            statement.sorts = [Sort(*tple) for tple in key_or_list]

        return statement

    def decode_skip(self, statement, skip):
        statement.offset = Offset(skip)
        return statement

    def decode_projection(self, statement, projection, columns):

        projection = projection or {}
        columns = [column for column in columns]
        columns_fields = [column.name for column in columns]
        mode = None
        for key, value in projection.items():
            try:

                index = columns_fields.index(key)
            except ValueError:
                pass
            else:
                if index is not None:

                    if value != mode and mode is not None:
                        raise ValueError(u"Projection can't use -1 and -1 at the same time.")

                    mode = value

                    if mode == 1:
                        statement.fields.append(columns[index])
                    else:
                        del columns[index]

        if mode == -1:
            statement.fields.fields = columns
        return statement

    def decode_query(self, collection, filters, projection, columns):
        select_statement = SelectStatement()
        select_statement = self.decode_projection(select_statement, projection, columns)
        select_statement.table = Table(collection)
        select_statement.where = self.decode_where(filters or {}, columns)
        return select_statement

    def get_column_from_name(self, columns, name):
        columns_fields = [column.name for column in columns]
        return columns[columns_fields.index(name)]

    def decode_where(self, filters, columns, parent=None):
        """
        Parse a filter from the API.
        Args:
            filters (dict): The filters to parse.
            parent (unicode): The parent operator to join filters ($and or $or).
        """
        if not parent:
            parent = Operator(u"and")

        if not isinstance(filters, list):
            filters = [filters]
        
        translated = []

        for filt in filters:
            for key, value in filt.items():
                if key in self._OPERATORS and parent is not None:

                    translated += [self.get_column_from_name(columns, parent), Operator(self._OPERATORS[key]), Value(value)]
                elif isinstance(value, dict):
                    translated += self.decode_where(filters=value, columns=columns, parent=key)
                else:
                    translated += [self.get_column_from_name(columns, key), Operator(u"="), Value(value)]

        return translated
