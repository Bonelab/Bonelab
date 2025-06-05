#!/usr/bin/env python
"""Graphical user interface."""

# import _mypath
import sys
import os
from PyQt6 import QtCore, QtWidgets
import logging
from redcap_dxa_converter import load_reference
from redcap_dxa_converter import Measurement
from redcap_dxa_converter import process_header
from redcap_dxa_converter import dict_datatypes
import codecs
import csv
from datetime import datetime


# logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %I:%M:%S %p', level=logging.INFO)  # time.strftime
class InputDialog(QtWidgets.QWidget):
    """QT4 GUI class."""

    def __init__(self, parent=None):
        """GUI init."""
        QtWidgets.QWidget.__init__(self, parent)
        # Window geometry and title
        self.setWindowTitle('Redcap Dxa Converter')

        # change directory to home
        home = os.path.expanduser("~")
        os.chdir(home)

        # ##########################
        # SELECT FILES AND FOLDERS
        # ##########################
        # Select Reference File button
        self.reference_button = QtWidgets.QPushButton('Redcap Reference', self)
        self.reference_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.reference_button.clicked.connect(self.selectReferenceClick)
        self.setFocus()
        # reference text box
        self.reference_label = QtWidgets.QLineEdit(self)

        # Select data File button
        self.data_button = QtWidgets.QPushButton('DXA Data', self)
        self.data_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.data_button.clicked.connect(self.selectDataClick)
        self.setFocus()
        # data text box
        self.data_label = QtWidgets.QLineEdit(self)

        # Select Output button
        self.output_button = QtWidgets.QPushButton('Output Folder', self)
        self.output_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.output_button.clicked.connect(self.selectFolderClick)
        self.setFocus()
        # output text box
        self.output_folder_label = QtWidgets.QLineEdit(self)

        # ########################################
        # FILE TYPE DROP DOWN BUTTON
        # ########################################
        # set default:
        self.data_type_label = 'Femur'
        # combo box
        self.data_type_dropdown = QtWidgets.QComboBox(self)
        self.data_type_dropdown.addItem('Femur')
        self.data_type_dropdown.addItem('Total Body')
        self.data_type_dropdown.addItem('Total Body Core')
        self.data_type_dropdown.addItem('Total Body Comp')
        self.data_type_dropdown.addItem('Spine')
        self.data_type_dropdown.addItem('Forearm')
        self.data_type_dropdown.activated[str].connect(self.set_data_type)

        # ########################################
        # DATE FORMAT DROP DOWN BUTTON
        # ########################################
        # set default:
        self.ref_dateformat = '%Y-%m-%d'
        # combo box
        self.ref_date_format_dropdown = QtWidgets.QComboBox(self)
        self.ref_date_format_dropdown.addItem('Select Date Format')
        self.ref_date_format_dropdown.addItem('2017-05-30')
        self.ref_date_format_dropdown.addItem('17-05-30')
        self.ref_date_format_dropdown.addItem('2017-Sep-30')
        self.ref_date_format_dropdown.addItem('17-Sep-30')
        self.ref_date_format_dropdown.addItem('30-05-2017')
        self.ref_date_format_dropdown.addItem('30-05-17')
        self.ref_date_format_dropdown.addItem('30-Sep-2017')
        self.ref_date_format_dropdown.addItem('30-Sep-17')
        self.ref_date_format_dropdown.activated[str].connect(self.set_ref_date_format)

        # ########################################
        # PROCESS THE FILES AND CLOSE THE WINDOW
        # ########################################
        # start button
        self.processButton = QtWidgets.QPushButton('Process!', self)
        self.processButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.processButton.clicked.connect(self.processButtonClick)
        self.setFocus()

        # Done button
        self.donebutton = QtWidgets.QPushButton('Done!', self)
        self.donebutton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.donebutton.clicked.connect(self.close)
        self.setFocus()

        # ########################################
        # CUSTOM LOGGER WINDOWS
        # ########################################
        # custom logger
        logTextBox = QPlainTextEditLogger(self)
        # logTextBox.setFormatter(logging.Formatter('%(asctime)s %(message)s', datefmt='%Y-%m-%d %I:%M:%S %p'))
        logTextBox.setFormatter(logging.Formatter('%(message)s'))
        logging.getLogger().addHandler(logTextBox)
        logging.getLogger().setLevel(logging.INFO)

        # ########################################
        # GRID LAYOUT
        # ########################################
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)
        grid.addWidget(self.reference_button, 0, 0)
        grid.addWidget(self.reference_label, 0, 1)
        grid.addWidget(self.data_button, 1, 0)
        grid.addWidget(self.data_label, 1, 1)
        grid.addWidget(self.output_button, 2, 0)
        grid.addWidget(self.output_folder_label, 2, 1)
        grid.addWidget(self.ref_date_format_dropdown, 0, 2)
        grid.addWidget(self.data_type_dropdown, 1, 2)
        grid.addWidget(self.processButton, 7, 2)
        grid.addWidget(self.donebutton, 8, 2)
        # grid.addWidget(self.textEdit, 2, 1, 6, 1)
        grid.addWidget(logTextBox.widget, 3, 1, 6, 1)
        self.setLayout(grid)
        # self.resize(600, 130)
        self.resize(900, 430)

        # #############################
        # SETUP PARAMETERS
        # #############################
        # set dateformat used for dates in SOURCE file
        self.output_dateformat = '%Y-%m-%d'
        self.data_dateformat = '%d/%b/%Y'
        Measurement.dateformat = self.data_dateformat

        # search window (days)
        self.window = 14  # +/- 14 days around measurement date

        # indes to insert recap_event column
        self.index = 1

    def set_data_type(self, data_type):
        """set dxa data type as string."""
        self.data_type_label = data_type

    def set_ref_date_format(self, date_format):
        """set dxa date format string."""
        if date_format == 'Select Date Format':
            self.ref_dateformat = '%Y-%m-%d'
        elif date_format == '2017-05-30':
            self.ref_dateformat = '%Y-%m-%d'
        elif date_format == '17-05-30':
            self.ref_dateformat = '%y-%m-%d'
        elif date_format == '2017-Sep-30':
            self.ref_dateformat = '%Y-%b-%d'
        elif date_format == '17-Sep-30':
            self.ref_dateformat = '%y-%b-%d'
        elif date_format == '30-05-2017':
            self.ref_dateformat = '%d-%m-%Y'
        elif date_format == '30-05-17':
            self.ref_dateformat = '%d-%m-%y'
        elif date_format == '30-Sep-2017':
            self.ref_dateformat = '%d-%b-%Y'
        elif date_format == '30-Sep-17':
            self.ref_dateformat = '%d-%b-%y'
        else:
            self.ref_dateformat = '%Y-%m-%d'

    def processButtonClick(self):
        """start script."""
        # print "date_type", str(self.data_type_label), len(str(self.data_type_label))
        # print str(self.output_folder_label.text()), len(str(self.output_folder_label.text()))
        # print str(self.reference_label.text()), len(str(self.reference_label.text()))
        # print str(self.data_label.text()), len(str(self.data_label.text()))
        if (len(str(self.reference_label.text())) == 0 or len(str(self.data_label.text())) == 0 or len(str(self.output_folder_label.text())) == 0):
            logging.warning("not all input fields were selected. Please select Reference, Data, and Output folder fields to continue")
        else:
            # read in reference
            refdict = load_reference(str(self.reference_label.text()), self.ref_dateformat)

            # create output path
            outputpath = create_output_file_path(str(self.output_folder_label.text()), str(self.data_type_label))

            # read in textfile (using codecs.open with utf-16 codex overcomes 0 byte issue)
            with codecs.open(str(self.data_label.text()), 'rb', 'utf-16') as f, open(outputpath, 'wb') as o:

                # read in data files
                data = csv.reader(to_utf8(f), delimiter="\t")
                logging.info('reading data from file: {0}'.format(str(self.data_label.text())))

                # output file writer
                output = csv.writer(o)
                logging.info('writing data to file: {0}'.format(outputpath))

                # header and indeces of columns to keep
                indeces = None
                new_header = None
                processed = 0

                # loop through rows of data file.
                for row in data:

                    # process header and subsequent rows
                    if (new_header is None and indeces is None and processed is 0):
                        # get new headers (update row) and indeces
                        new_header, indeces = process_header(row, dict_datatypes[str(self.data_type_label)])

                        # warn that wrong file was used
                        if (len(new_header) == 0 and len(indeces) == 0):
                            logging.error('not matching header found. Check if correct file type selected!')
                            sys.exit(app.exec_())

                        # insert column for redcap_event header
                        new_header.insert(self.index, 'redcap_event_name')
                        output.writerows([new_header])
                        continue
                    else:
                        # only keep data in row that you actually want to keep.
                        row = [val for ind, val in enumerate(row) if ind in indeces]

                    # create a Measurement
                    try:
                        temp = Measurement(row[0].strip(), row[1].strip())
                    except ValueError:
                        logging.warning('date field does not match date format')
                        row.insert(self.index, Measurement.flag_no_event)  # Treat as not date was found.
                        output.writerows([row])
                        continue

                    # search reference, skip line if study_id NOT ind reference file.
                    try:
                        ref_results = refdict[temp.study_id]
                    except KeyError:
                        logging.warning('Study ID {0} was not found in redcap reference file'.format(temp.study_id))
                        continue

                    # calculate time differente between measurement date and reference datestring
                    t_diff = list()
                    for event, dateobject in ref_results:
                        delta = temp.date - dateobject
                        t_diff.append((event, abs(delta.days)))

                    # check if there are entries match a event date OR within the time window
                    ref_targets = []
                    ref_targets = [event for event, diff in t_diff if diff == 0]  # check if in window

                    if not ref_targets:  # if no perfect matches were found search for match inside window
                        ref_targets = [event for event, diff in t_diff if diff <= self.window]

                    # process returned event list (implement how to handle it)
                    try:
                        temp.process_event_list(ref_targets)
                    except TypeError:
                        raise NotImplementedError
                    else:
                        logging.debug('StudyID: {0}, Event: {1}'.format(temp.study_id, temp.redcap_event))

                    # update date to desired string
                    row[1] = temp.date.strftime(self.output_dateformat)

                    # remove units: split string by white space and
                    # select 1 output. There are no string in data.
                    logging.debug('processing row: {0}'.format(row))
                    row = map(lambda x: str(x).partition(" ")[0], row)

                    # remove '%' from units without space between number and %
                    row = map(lambda x: str(x).partition("%")[0], row)

                    # place returned value into row of data
                    row.insert(self.index, temp.redcap_event)
                    logging.debug('writing row: {0}'.format(row))
                    output.writerows([row])

                logging.info('Done processing!')

    def selectFolderClick(self):
        """display folder path."""
        directory_name = str(QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Directory'))
        self.output_folder_label.setText(unicode(directory_name))

    def selectReferenceClick(self):
        """display file path."""
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select file', 'home')
        self.reference_label.setText(unicode(str(filename)))

    def selectDataClick(self):
        """display file path."""
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select file', 'home')
        self.data_label.setText(unicode(str(filename)))


class QPlainTextEditLogger(logging.Handler):
    """custom handler."""

    def __init__(self, parent):
        """init."""
        logging.Handler.__init__(self)
        self.widget = QtWidgets.QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        """emit."""
        msg = self.format(record)
        self.widget.appendPlainText(msg)


def create_output_file_path(path, label):
    """create path to new output file.

    Args:
        path (str): path to output folder (from GUI)
        label (str): type of data selected (from GUI)

    Returns:
        filepath (str): combined new name, with selected path
    """
    output_name = 'PROCESSED_' + label + '_' + datetime.today().strftime('%Y-%m-%d') + '.csv'
    filepath = os.path.join(path, output_name)
    logging.info("creating file: {0} in location: {1}".format(output_name, path))
    return filepath


def to_utf8(fp):
    """convert file to uft8."""
    for line in fp:
        yield line.encode("utf-8")


app = QtWidgets.QApplication(sys.argv)
icon = InputDialog()
icon.show()
app.exec_()
