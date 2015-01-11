__author__  = 'MyNameIsMeerkat'
__version__ = '0.1'
__date__    = 'Jan 11 2015'
__license__ = "GPLv3"

import os
import sys
import IPS

class IpsMulti(object):
    """
    Walk a dir structure looking for ROM files and create IPS files for them against a common base ROM image
    """
    def __init__(self, base_rom, starting_dir, output_dir, debug = False):
        """

        :param base_rom: String - The rom image against which all others will be patched
        :param starting_dir: String - The dir head that will be walked looking for other ROM files
        :param output_dir: String - The dir under which generated IPS files will be saved
        :param debug: Boolean - verbose output, is passed into IPS class
        :return:
        """
        ##List of files considered ROMs eligable for IPS generation
        self.rom_exts      = [".smc", ".sfc", ".bin"]

        ##The rom image against which all others will be patched
        self.base_rom_path = base_rom

        ##The dir head that will be walked looking for other ROM files
        self.starting_dir  = starting_dir

        ##The dir under which generated IPS files will be saved
        self.output_dir    = output_dir

        ##Be noisy?
        self.debug         = debug

        ##
        self.banner = """\n~~* IpsMulti v%s by %s *~~\n[Latest versionat: https://github.com/MyNameIsMeerkat/RetronPy]\n"""%(__version__, __author__)


    def __call__(self):
        """
        Walk through a dir and it's sub_dirs and create an IPS file against the base ROM for every other ROM found
        Instantiate a new IPS class for each ROM and use it to generate the patch file

        :return:
        """
        print self.banner

        for root, dirs, files in os.walk(self.starting_dir):

            out_dir = os.path.join(self.output_dir, root[len(self.starting_dir)+1:])

            ##Mirroring Dir structure in output dir
            try:
                print "[!] Making dir: %s ..... "%(out_dir),
                os.makedirs(out_dir)
                print "done.\n"
            except OSError, err:
                if err.errno == 17:
                    ##Dir already exists
                    print "Already exists.\n"
                else:
                    raise

            ##For each file that is a known ROM type create an IPS patch against the base image
            for f in files:
                if os.path.splitext(f)[1] in self.rom_exts:
                    #print "Creating IPS for %s against %s"%(f, self.base_rom_path)

                    new_rom_path = os.path.join(root, f)
                    ips_path = os.path.join(out_dir, os.path.splitext(f)[0])+".ips"

                    ##Create the IPS object to do the hard work
                    ips_obj = IPS.IPS(self.base_rom_path, new_rom_path, ips_path, self.debug)
                    ret = ips_obj()
                    print ""


if __name__ == "__main__":

    ##Quick n dirty cmd line parsing - no error checking or cmdline switches, lazy :)
    base_rom  = os.path.abspath(os.path.expanduser(os.path.expandvars(sys.argv[1])))
    start_dir = os.path.abspath(os.path.expanduser(os.path.expandvars(sys.argv[2])))
    out_dir   = os.path.abspath(os.path.expanduser(os.path.expandvars(sys.argv[3])))

    ipsm = IpsMulti(base_rom, start_dir, out_dir)
    ipsm()