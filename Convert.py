'''
Word search.

Copyright (C) 2020 Francis J. Hammell <hammell.francis@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

There is a copy of this license at <http://www.gnu.org/licenses/>.

Created on 09 Feb 2020

@author: fjh
'''
import sys
import os, fnmatch
import glob
import datetime
import logging

class Convert:
    '''
    '''
    logger = logging.getLogger(__name__)
    FILE_EXTENSION = "*.qif"
    RECORD_DELIMITER = "^"
    # {'^', 'S', '!Type:Invst\n', 'E', '$', '!Type:Cash\n', 'L', '!Type:Bank\n', 'C', 'P', 'M', '!Type:CCard\n', '!Type:Oth A\n', 'N', 'Q', 'Y', 'I', 'D', 'T'}

    DETAIL_CODES_DICT_TITLES = {"I": "Price",
                                "C": "Cleared",
                                "P": "Description",
                                "Y": "Security",
                                "D": "Date",
                                "Q": "Quantity",
                                "T": "Amount (£)",
                                "N": "Number",
                                "L": "Category",
                                "M": "Memo"}

    DETAIL_CODES_DICT = {"I": "Price.",
                        "C": "Cleared status. Values are blank (unreconciled/not cleared), '*' or 'c' (cleared) and 'X' or 'R' (reconciled).",
                        "P": "Payee. Or a description for deposits, transfers, etc.",
                        "S": "Split category. Same format as L (Categorization) field. (40 characters maximum).",
                        "$": "Amount transferred, if cash is moved between accounts.",
                        "Y": "Security name.",
                        "D": "Date. Leading zeroes on month and day can be skipped. Year can be either 4 digits or 2 digits or 6 (=2006).",
                        "E": "Split memo—any text to go with this split item.",
                        "Q": "Quantity of shares (or split ratio, if Action is StkSplit).",
                        "T": "Amount of the item. For payments, a leading minus sign is required. For deposits, either no sign or a leading plus sign is accepted. Do not include currency symbols ($, £, ¥, etc.). Comma separators between thousands are allowed.",
                        "N": "Number of the check. Can also be 'Deposit', 'Transfer', 'Print', 'ATM', 'EFT'.",
                        "L": "Category or Transfer and (optionally) Class. The literal values are those defined in the Quicken Category list. SubCategories can be indicated by a colon (':') followed by the subcategory literal. If the Quicken file uses Classes, this can be indicated by a slash ('/') followed by the class literal. For Investments, MiscIncX or MiscExpX actions, Category/class or transfer/class. (40 characters maximum).",
                        "M": "Memo—any text you want to record about the item."}

    HEADER_DICT = {"!Type:Invst": "Investing: Investment Account.",
                    "!Type:Cash": "Cash Flow: Cash Account.",
                    "!Type:Bank": "Cash Flow: Checking & Savings Account.",
                    "!Type:CCard": "Cash Flow: Credit Card Account.",
                    "!Type:Oth A": "Property & Debt: Asset."}

    def __init__(self):
        '''
        Constructor
        '''
        self.codes = set()

    def convert_to_csv(self, files_location):
        '''Convert the files to CSV format.
        '''
        print("Converting...")
        self.files_list = self._get_files(files_location)
        print(self.files_list)
        for f in self.files_list:
            records_list = self._split_into_records(files_location, f)
            header_type, header_lines, detail_records = self._parse_records(records_list)
            # Print...
            self._write_file(files_location, f, header_type, header_lines, detail_records)

    def _write_file(self, files_location, f, header_type, header_lines, detail_records):
        '''
        '''
        out_name = f.rstrip(self.FILE_EXTENSION[1:])
        with open(os.path.join(files_location, out_name + ".asv"), "w") as out:
            
            if header_type == "!Type:Bank":
                self._write_file_header(out, header_type)
                self._write_file_header_lines_bank(out, header_lines)
                self._write_file_detail_lines_bank(out, detail_records)

            elif header_type == "!Type:Cash":
                self._write_file_header(out, header_type)

            elif header_type == "!Type:Invst":
                self._write_file_header(out, header_type)

            elif header_type == "!Type:CCard":
                self._write_file_header(out, header_type)

            elif header_type == "!Type:Oth A":
                self._write_file_header(out, header_type)

            else:
                pass


    def _write_file_header(self, out, header_type):
        '''
        '''
        out.write (self.HEADER_DICT[header_type] + "\n")

    def _write_file_header_lines_bank(self, out, header_lines):
        '''
        '''
        out.write ("{0}^{1}^{2}^{3}^{4}\n".format(header_lines["T"],
                                            header_lines["D"],
                                            header_lines["P"],
                                            header_lines["C"],
                                            header_lines["L"]))

    def _write_file_detail_lines_bank(self, out, detail_records):
        '''
        '''
        for record in detail_records:
            out.write ("{0}^{1}^{2}^{3}^{4}^{5}^'{6}'^{7}^{8}^{9}\n".format(record["T"],
                                                                    record["D"],
                                                                    record["P"],
                                                                    record["C"],
                                                                    record["N"],
                                                                    record["L"],
                                                                    record["M"],
                                                                    record["E"],
                                                                    record["S"],
                                                                    record["$"]))

    def _get_files(self, files_location):
        '''Get a list of the files.
        '''
        return fnmatch.filter(os.listdir(files_location), Convert.FILE_EXTENSION)

    def _split_into_records(self, files_location, f):
        '''...
        '''
        records = open(os.path.join(files_location, f), "r")
        records_list = []
        record = ""
        for line in records:
            if line[0] == self.RECORD_DELIMITER:
                records_list.append(record)
                record = ""
            else:
                record = record + line

        return records_list

    def _parse_records(self, records_list):
        '''...
        '''
        header = records_list.pop(0)
        (header_type, header_lines) = self._get_header(header)
        detail_records = self._get_items(records_list)
        return [header_type, header_lines, detail_records]
        
    def _get_items(self, records_list):
        '''...
        '''
        detail_records = []
        item_lines = {"I": "",
                    "C": "",
                    "P": "",
                    "Y": "",
                    "D": "",
                    "Q": "",
                    "T": "",
                    "N": "",
                    "L": "",
                    "M": "",
                    "$": "",
                    "E": "",
                    "S": ""}

        for line in records_list:
            items = line.splitlines()
            for item in items:
                first_char = item[0]
                formatted = self._switch(first_char, item)

                if first_char in "SE$":
                    item_lines["M"] = item_lines["M"] + " " + formatted
                    if first_char in "$":
                        item_lines["M"] = item_lines["M"] + " - "
                else:
                    item_lines[first_char] = formatted

            # detail_records.append(item_lines.copy())
            detail_records.append(item_lines)
            item_lines = {"I": "",
                        "C": "",
                        "P": "",
                        "Y": "",
                        "D": "",
                        "Q": "",
                        "T": "",
                        "N": "",
                        "L": "",
                        "M": "",
                        "$": "",
                        "E": "",
                        "S": ""}


        return detail_records

    def _get_header(self, header):
        '''...
        '''
        lines = header.splitlines()
        header_type = lines.pop(0)

        if not header_type in self.HEADER_DICT.keys(): 
            raise ValueError("The account type cannot be read.")

        header_lines = {"I": "",
                            "C": "",
                            "P": "",
                            "Y": "",
                            "D": "",
                            "Q": "",
                            "T": "",
                            "N": "",
                            "L": "",
                            "M": ""}
        for line in lines:
            first_char = line[0]
            formatted = self._switch(first_char, line)
            header_lines[first_char] = formatted

        return [header_type, header_lines]

    def _switch(self, first_char, line):
        '''Format line.
        '''
        formatted = line[1:].strip()
        self.codes.add(first_char)

        if first_char == "!":
            return formatted
        elif first_char == "I":
            return formatted
        elif first_char == "C":
            return formatted
        elif first_char == "P":
            return formatted
        elif first_char == "S":
            return formatted
        elif first_char == "$":
            return formatted
        elif first_char == "Y":
            return formatted
        elif first_char == "D":
            # "D5/15'2019"
            if formatted.count("/") > 1:
                month, day, year = map(int, formatted.split("/", 2))
            else:
                month_str, day_year = map(str, formatted.split("/", 1))
                month = int(month_str)
                day, year = map(int, day_year.split("'"))

            formatted = datetime.datetime(year=year, month=month, day=day)
            formatted= formatted.strftime("%d/%m/%Y")

            return formatted
        elif first_char == "E":
            return formatted
        elif first_char == "Q":
            return formatted
        elif first_char == "T":
            return formatted
        elif first_char == "N":
            return formatted
        elif first_char == "L":
            return formatted
        elif first_char == "M":
            return formatted
        elif first_char == self.RECORD_DELIMITER:
            # Throw exception.
            return formatted
        else:
            print(line)