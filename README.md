# RetronPy
A collection of Python tools / libraries useful for manipulating ROMs &amp; IPS files for use with the [Retron](http://hyperkin.com/Retron5/) console from Hyperkin.

I began writing them as there didn't seem to be any good cross-platform IPS generation tools or base IPS functionality upon which to extend and build useful ROM utilities.

They are shared as others may find them useful for their own projects.

More libraries and utilities will get added as and when I need to do something new.


##Retron 5 IPS based ROM patching

The use case for the IPS tools is if you are wanting to generate IPS files against a phsyical cart in the Retron system and then use IPS patch menu to replace the physical cartridges image with that of a different ROM entirely.

*If you are unsure, a video explaining how to apply IPS patch files on the Retron console by twfdisturbed is [here](https://www.youtube.com/watch?v=w5Kbv4i_q60).*

**Disclaimer**

```
You should only generate IPS files against images of ROMs you legally own or that are no longer under copyright and freely available. Using these tools for pirating ROMs is bad mmmkay 
```

##IpsMulti

IpsMulti uses the `IPS.py` class to be able to generate IPS patch files for all ROM files found in a directory structure beneath a given starting point. All discovered ROM files have IPS files generated against a supplied *base rom* file.

This allows you to quickly generate a large number of IPS files against the image of a physcial cartridge you own from a directory structure that is full of other ROM images. You can then pop all of the IPS files on your SDCard and access them on the Retron and apply them against the physical cartridge you have inserted into the console.

Using IpsMulti is simple:

```
$ python IpsMulti.py <base_rom_path> <directory_of_roms_to_walk> <directory_to_output_ips_files>
```

* **base_rom_path**: The ROM image against which all other discovered ROMs should be diff'd (this should be the image of a physical ROM you own and that is jammed into your Retron)
* **directory_of_roms_to_walk**: This is the directory within which are all the ROM images you want to create IPS files for
* **directory_to_output_ips_files**: This is the directory where you would like all the generated IPS files to be dumped to (it is this directory that you then put on your SDCard and plug into your Retron)

IpsMulti will maintain the directory structure from the ROM input directory in the IPS output directory in an effort to keep things organised.

ROM files eligable for IPS patch generation are recognised by their extension, currently `.smc`, `.sfc` and `.bin` are extensions that are presumed to be ROMs and that will have an IPS file creatd for them. If you have other files that you want to patch add their extension to the `self.rom_exts` list in the `IpsMulti` class.


##IPS.py

```
IPS patch application is currently todo, this class can only generate an IPS file at this time
```

An extensible class to **generate** IPS [format](http://romhack.wikia.com/wiki/IPS) patch files from two ROM images. This is intended to be usable by other applications that need to do IPS shenanigans without wanting to wory about the horrible details themselves.

The class was written with quite a bit of inline documentation to also act as a general IPS file format resource for those wanting to have an example implementation of the *spec* to follow. 

Quick and dirty test functionlity is included to allow commandline IPS path generateion from two supplied ROM images.

```
$ python IPS.py <orig_rom_path> <new_rom_path> <ips_output_path>
```

This will create an IPS patch file by diff'ing the rom file at `new_rom_path` against the rome file at `orig_rom_path` and saving the resulting IPS file to `ips_output_file`. 

The origins of this class began by looking at [ips.py](https://github.com/fbeaudet/ips.py) from [fbeaudet](https://github.com/fbeaudet) but then diverged quite a bit fixing a number of bugs, corner cases, being object oriented, and working with both Python 2.x and 3.x.


##Platforms
The utilities should run under OS X, Linux and Windows (though Windows support is far from well tested.....).

They should also support Python 2.x and 3.x equally.

##Bugs
Probably lots, if you find them create an [issue](https://github.com/MyNameIsMeerkat/RetronPy/issues) and I'll try and fix.
