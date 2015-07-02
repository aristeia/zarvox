Windows Build Instructions for TunePimp
=======================================

Required Software:
~~~~~~~~~~~~~~~~~~

In order to compile libtunepimp for Windows, you will need to install 
and compile a number of other open source packages. Each of these
packages needs to be in the proper location in order for TunePimp
to compile. Place each of these source distributions right next
to the tunepimp sources. For example, if you are installing libmad, 
and your tunepimp source is located in c:\musicbrainz\tunepimp, then 
place the source for libmad in c:\musicbrainz\libmad.

   libmusicbrainz -- MusicBrainz Client Library (http://musicbrainz.org/products/client/download.html)
   ---------------------------------------------------------------------------------------------------
   
   This is the underlying library that tunepimp uses to communicate 
   with the MusicBrainz server. Download this library to a
   directory called 'mb_client', compile and then place the
   musicbrainz.lib file into the tunepimp\win32 directory.


   MAD (http://www.underbit.com/products/mad)
   ------------------------------------------
   
   This is the MP3 audio decoder from Underbit. Download
   the source code and save it in a directory called 'libmad'.
   Compile the static libmad.lib file and place it into
   the tunepimp\win32 directory.
   
   Ogg/Vorbis/Vorbisfile (http://vorbis.com)
   -----------------------------------------
   
   This is the Ogg/Vorbis audio decoder from xiph.org. Download
   the windows source SDK (NOT THE BINARY SDK) and save the ogg
   source into 'libogg' and the vorbis source into 'libvorbis'
   Then open the Visual Studio project files and each of the 
   'dynamic' sub projects set the runtime library to: 
   
      Multithreaded /MT
   
   (See configuration properties, C/C++, Code generation, Runtime 
    library in VS .NET)
   
   The compile the ogg, vorbis and vorbisfile projects under
   Release mode. Copy the resultant .lib files generated for each 
   of the dlls into the tunepimp\win32 directory.
   
   FLAC (http://flac.sourceforge.net)
   ----------------------------------
   
   This is the FLAC audio decoder. Download and save into
   'libflac'. Set the 'dynamic' subprojects run time library to 
   Multithreaded /MT as mentioned in the Ogg/Vorbis section 
   (IMPORTANT!!). Then follow the remaining compile instructions 
   from the FLAC distribution. Copy the resultant libFLAC.lib 
   file to the tunepimp\win32 directory.
   
   Patch for UNICODE support - http://musicbrainz.org/~luks/flac-win32.diff
   
   TagLib 1.4 (http://developer.kde.org/~wheeler/taglib.html)
   ----------------------------------------------------------
   
   Patch for UNICODE support - http://musicbrainz.org/~luks/taglib-win32.diff
   
   MP4v2 (http://mpeg4ip.sourceforge.net/downloads/index.php)
   ----------------------------------------------------------
   
   Patch for UNICODE support - http://musicbrainz.org/~luks/mp4v2-win32.diff
   
If you get header file not found problems or library file not found
problems, then check the locations of the libraries from above.

Building TunePimp:
~~~~~~~~~~~~~~~~~~

Once you've completed the painstaking process of collecting the
sources and copying the .lib files to tunepimp\win32, then you
can beging compiling tunepimp itself. If you carried out the 
steps above correctly, this should not be a big deal.

If for some reason you do not want to build support for all
the formats listed above, then edit the tunepimp\config_win32.h
file and comment out the appropriate #define HAVE_xxxx lines.

Simply open the tunepimp\win32\tunepimp.sln project file and
build the project. The first step in the build process is to 
copy the tunepimp\config_win32.h file to config.h and the
compile all the files in tunepimp\lib, tunepimp\lib\threads\win32 
and tunepimp\lib\id3tag into one DLL.

Once the project has built you will need to copy all the needed
DLLs from the projects above and the tunepimp.dll into your
application directory. 

TunePimp API documentation:
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The documentation for the TunePimp API is inline with the
tp_c.h header file and can be built into nice readable
web pages by the doxygen tool. Simply run the doxygen
tool with the tunepimp\tunepimp.doxy file to generate the
documentation. Doxygen is available from:

  http://www.doxygen.org/
  
  
