__author__  = 'MyNameIsMeerkat'
__version__ = '0.1'
__date__    = 'Jan 11 2015'
__license__ = "GPLv3"

#Todo - Include IPS patch application not just creation
#Todo - Proper exception generation / handling - lazy

import os
import sys
import gzip
import struct
import collections

##Avoid need for shutil.disk_usage in Python 3.4 (Recipe from http://code.activestate.com/recipes/577972-disk-usage/)
_ntuple_diskusage = collections.namedtuple('usage', 'total used free')

if hasattr(os, 'statvfs'):  # POSIX
    def disk_usage(path):
        st = os.statvfs(path)
        free = st.f_bavail * st.f_frsize
        total = st.f_blocks * st.f_frsize
        used = (st.f_blocks - st.f_bfree) * st.f_frsize
        return _ntuple_diskusage(total, used, free)

elif os.name == 'nt':       # Windows
    import ctypes
    import sys

    def disk_usage(path):
        _, total, free = ctypes.c_ulonglong(), ctypes.c_ulonglong(), \
                           ctypes.c_ulonglong()
        if sys.version_info >= (3,) or isinstance(path, unicode):
            fun = ctypes.windll.kernel32.GetDiskFreeSpaceExW
        else:
            fun = ctypes.windll.kernel32.GetDiskFreeSpaceExA
        ret = fun(path, ctypes.byref(_), ctypes.byref(total), ctypes.byref(free))
        if ret == 0:
            raise ctypes.WinError()
        used = total.value - free.value
        return _ntuple_diskusage(total.value, used, free.value)
else:
    raise NotImplementedError("platform not supported")
##/end



class IPS(object):
    """
    Class to do IPS patch generation & application (todo) to ROM files
    File spec here: http://romhack.wikia.com/wiki/IPS
    """

    def __init__(self, original_file, new_file, ips_file, debug = False):
        """
        Init this thang
        """
        #16MB Max size of an IPS file - 3byte int
        self.FILE_LIMIT    = 0xFFFFFF

        ## Max size of an individual record - 2 byte int
        self.RECORD_LIMIT  = 0xFFFF

        ##IPS file header 'PATCH'
        self.PATCH_ASCII   = b"\x50\x41\x54\x43\x48"

        ##IPS file footer 'EOF'
        self.EOF_ASCII     = b"\x45\x4f\x46"
        self.EOF_INTEGER   = 4542278

        ##The files we will be working with
        self.original_path = original_file
        self.new_path      = new_file
        self.ips_path      = ips_file

        ##Accounting variables
        self.curr_offset   = 0
        self.record_count  = 0
        self.patch_size    = 0

        ##Be noisy?
        self.debug         = debug


    def __call__(self):
        """
        Demo of the class, generate an IPS file from 2 given ROMs

        :param original_file: File against which new_file will be diff'd and IPS created
        :param new_file: File with which original_file will be diff'd and IPS created
        :param ips_file: Where the IPS file will be saved
        """
        ##Open up the files
        self._setup_files()

        print "[+] Creating IPS patch between %s and %s"%(self.original_path, self.new_path)
        ret = self.create_ips()

        if False in ret:
            print "[-] Something went wrong :("
            print "\t%s"%(ret[1])
        else:
            print "[+] Written %d IPS records to a patch %d (0x%x) bytes in size"%(self.record_count, self.patch_size, self.patch_size)
            print "[+] IPS file location: %s"%(self.ips_path)


    def _debug(self, msg):
        """
        Debug output
        :param msg: String to display
        :return:
        """
        if self.debug:
            print "[!] %s"%(msg)


    def __check_types(self):
        """
        Check if the supplied file variables make sense

        :return: success - Boolean
        """
        assert type(self.original_path) is type(''), '\'original_file\' must be a string.'
        assert type(self.new_path) is type(''), '\'modified_file\' must be a string.'
        assert type(self.ips_path) is type(''), '\'patch_file must\' be a string.'


    def __check_disk_space(self, file_to_check):
        """
        Check sufficient disk space available to write to

        :param file_to_check: File to check sufficient space to write
        :return: tuple - (Boolean - success, String - Error message)
        """
        directory =  os.path.dirname(os.path.abspath(file_to_check))
        if directory == '' :
            directory = '.'

        if disk_usage(directory).free <=  self.FILE_LIMIT:
            return (False, 'Not enough space for creating a patch at specified path.')
        else:
            return (True, "")


    def _setup_files(self):
        """
        Open and check file we will be using
        :return:
        """
        ##Basic paths sanity check
        self.__check_types()

        ## File object containing the original (base) ROM data
        try :
            self.original_data = open(self.original_path, 'rb').read()
        except :
            return (False, 'There was a problem trying to read \'original_file\'.')

        ## File object containing the ROM data of the ROM we want to diff against the base to produce the IPS patch
        try :
            self.modified_data = open(self.new_path, 'rb').read()
        except :
            return (False, 'There was a problem trying to read \'new_file\'.')

        ## File object for writing the IPS data to
        try :
            self.patch_file_obj = open(self.ips_path, 'wb')
        except :
            return (False, 'There was a problem trying to write to \'patch_file\'.')


        ## The IPS file format has a size limit of 16MB
        if len(self.modified_data) > self.FILE_LIMIT :
            return (False, 'Modified file is too large for IPS format. Max: 16MB.')

        ## Check there is enough disk space to write the IPS data to (could be a problem seen on SD cards etc)
        ret = self.__check_disk_space(self.ips_path)[0]
        if not ret:
            return ret

        return (True, "Success")



    def write_record(self, record_data, overide_size = 0):
        """
        Method that takes relevant data and write an IPS record (non-RLE encoded)

        Format looks like (all integers in BIG endian):
        [OFFSET into file : 3bytes][SIZE of record : 2bytes][BYTES : SIZEbytes]

        :param patch_file_obj: FileObject - IPS file to which to write data
        :param record_data: ByteArray - Record data to write to the record object
        :param offset: Integer - Absolute offset into the original file the record refers

        :return:
        """
        ## Write the record to the IPS patch file

        ##Encode record's absolute offset into the original ROM,
        ##(IPS file format uses big endian 3-byte int, hence a truncated long, yuck!)
        self.patch_file_obj.write(struct.pack(">L", self.curr_offset)[1:])

        ##Encode size of record
        if not overide_size:
            self.patch_file_obj.write(struct.pack(">H", len(record_data)))
        else:
            self.patch_file_obj.write(struct.pack(">H", overide_size))

        ##Write the data
        self.patch_file_obj.write(record_data)

        ##Do some accounting
        self.record_count += 1
        self.patch_size += len(record_data) + 5



    def create_ips(self):
        """
        Creates an IPS patch file between the original and the specified file.
        The IPS format is just a binary diff between the two ROMs that is formatted into 'records' with a simple header

        :param original_file: File against which new_file will be diff'd and IPS created
        :param new_file: File with which original_file will be diff'd and IPS created
        :param ips_file: Where the IPS file will be saved
        :return: Tuple (Boolean: success, String: Message)
        """
        record_begun = False
        record       = bytearray()

        ## IPS file header
        self.patch_file_obj.write(self.PATCH_ASCII)
        self.patch_size += len(self.PATCH_ASCII)

        ## Write the IPS record(s), format looks like (all integers in BIG endian):
        ##  [OFFSET into file : 3bytes][SIZE of record : 2bytes][BYTES : SIZEbytes]

        ## Diff bytes between the new ROM and the base ROM, 1 byte at a time
        for pos in range(len(self.modified_data)):

            ##Are we starting to write a new record?
            if not record_begun:

                if len(self.original_data) <= pos or self.modified_data[pos] != self.original_data[pos]:
                    ##Start new record
                    record_begun = True
                    record       = bytearray()

                    ##From http://romhack.wikia.com/wiki/IPS in 'Caveats' section:
                    #
                    ## The number 0x454f46 looks like "EOF" in ASCII, which is why a patch record must never begin at
                    #  offset 0x454f46. If your program generates a patch record at offset 0x454f46, then you have a bug,
                    #  because IPS patchers will read the "EOF". One possible workaround is to start at offset 0x454f45
                    #  and include the extra byte in the patch.
                    ##
                    #  If a patch provides multiple values for the same byte in the patched file, then the IPS patcher
                    # may use any of these overlapped values. Also, if the patch extends the size of the patched file,
                    # but does not provide values for all bytes in the extended area, then the IPS patcher may fill the
                    # gaps with any values. A better IPS file provides no such overlapped values and no such gaps,
                    # though this is not a requirement of the IPS format.
                    if pos == self.EOF_ASCII:
                        record.append(self.modified_data[pos-1])

                    ##Add the byte from the new ROM at address 'a' to the record
                    record.append(self.modified_data[pos])

                    ##Save the absolute offset for this record
                    self.curr_offset = pos

                    ##Corner case - should never hit for real ROMs me thinks
                    ## If we're at the last address, close the record & write to the patch file
                    if pos == len(self.modified_data) - 1:
                        record_begun = False
                        self.write_record(record, overide_size = 0x01)


            ##We are continuing to write a current record
            else:

                ##Records have a max size of 0xFFFF as the size header is a short
                ## Check our current position and if we at the max size end the record and start a new one
                if len(record) == self.RECORD_LIMIT -1:
                    self._debug("Truncating overlong record: %s %s"%(len(record), hex(len(record))))

                    record_begun = False
                    record.append(self.modified_data[pos])
                    self.write_record(record)

                ##Append diff data to the record
                elif (len(self.original_data) <= pos or self.modified_data[pos] != self.original_data[pos]) and pos !=  len(self.modified_data) - 1:
                    ##Continue Record
                    record.append(self.modified_data[pos])

                ##END OF RECORD
                ## If we're at the last address of the new ROM, the bytes at the address are identical in both ROMs,
                ## or the base ROM  is longer than the address we are at in the modified ROM close the record
                else:
                    record_begun = False
                    self.write_record(record)

        ##Add the footer to the IPS file and flush the data to disk & close entire IPS file
        self.patch_file_obj.write(self.EOF_ASCII)
        self.patch_size += len(self.EOF_ASCII)
        self.patch_file_obj.close()

        return (True, 'Success')


if __name__ == '__main__':
    #Quick n dirty testing
    ips = IPS(sys.argv[1], sys.argv[2], sys.argv[3], debug=True)
    ips()
