I2D network creation

geti2dint.sh searches for a sources directory containing the source file for each organism, 
and a data file for each organism in the current directory. These are defined in the 
geti2dint.sh script itself. Eg:

    getInteractions fly ./sources/FLY.src ./i2d.FLY.tab
    getInteractions human ./sources/HUMAN.src ./i2d.HUMAN.tab
    getInteractions mouse ./sources/MOUSE.src ./i2d.MOUSE.tab
    getInteractions worm ./sources/WORM.src ./i2d.WORM.tab
    getInteractions yeast ./sources/YEAST.src ./i2d.YEAST.tab

Data file:
Contains the actual data with columsn Dataset, SwissProt1, SwissProt2

Source file:
 * Contains only the Dataset column from the data file; eg: BIND, BIND_Fly, CORE_1, etc.
 * This can be obtained by: geti2dsrc.sh i2d.organism.tab > ORGANISM.src

Once the data and source files are available, we can generate the interaction files. 
This example assumes the following directory hierarchy:

    ./
      |_ geti2dint.sh
      |_ geti2dsrc.sh
      |_ i2d.FLY.tab
      |_ i2d.HUMAN.tab
      |_ i2d.MOUSE.tab
      |_ i2d.WORM.tab
      |_ i2d.YEAST.tab
      |_ sources/
              |_ FLY.src
              |_ HUMAN.src
              |_ MOUSE.src
              |_ WORM.src
              |_ YEAST.src

To generate the i2d networks, just run geti2dint.sh. A directory named after the organism 
will be created in the current working directory. This directory will contain files named by 
sources. Each file will contain the results of the analysis. A special file under_threshold.txt 
will also be created containing interactions that are under the defined threshold. 

There is a special case regarding the sources WranaLow, WranaMedium, WranaHigh, StelzlLow, and StelzlMedium.
Wrana* networks are combined into one group called WranaGroup, and StelzlLow and StelzlMedium are combined 
into one group called StelzlLowMed.

An example of how the output directory and files will look like:

    ./
      |_ fly/
          |_ BIND
          |_ BIND_Fly
          |_ BIND_Mouse
          |_ BIND_Rat
          |_ BIND_Worm
          |_ Biogrid_Yeast
          |_ ...
          |_ under_threshold.txt
      |_ human/
          |_ BIND
          |_ BIND_Fly
          |_ BIND_Mouse
          |_ BIND_Rat
          |_ BIND_Worm
          |_ Biogrid_Yeast
          |_ ...
          |_ under_threshold.txt

The threshold can be adjusted by editing the value of the THRESHOLD variable in geti2dint.sh.

