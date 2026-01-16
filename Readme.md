parse\_pc80b\_v5.py



\##Tool to convert .dat files created by a toy ECG machine Easy ECG PC-80B into .csv format.



PC-80B is sold under different names.

Sample user manual can be found e.g. at https://www.creative-sz.com/products/lepu-pc-80b-portable-ecg-monitor-easy-ekg-machine-handheld/.



Available documentation claims that this device performs continuous ECG recording up to 12 hours long.

In reality this device creates a set of 30 sec recordings of ECG waveform.
Each 30 sec record has a header and a trailer.
These trailers and headers are present in between all such 30 sec records.
Delay between completion of a previous 30 sec record and the start of the next one is unknown.



These .dat files use proprietary binary format.

Documentation of this format is not available from a manufacturer.
Partial documentation of this file format is available on https://github.com/majbthrd/easyecg2gdf.

In these .dat files ECG waveform is stored as 12 bit value with upper 4 bits containing quality of signal/contact information.
Specification of the data in the upper 4 bits is unknown.



To create better waveform graphics this script sets values of signal in a trailer and in a header to 70% of min\_signal in he first 20 seconds of recording.



\##Sample Usage



python parse\_pc80b\_v5.py 20250105-10.dat --header-size 512 --trailer-size 512 --samplerate 150



In the above example:

20250105-10.dat    - name of a data file to process

--header-size 512  - header size of each record is 512 bytes

--trailer-size 512 - trailer size of each record is 512 bytes

--samplerate 150   - sampling rate is 150 readings/sec



All these parameters (except input file name) are optional and given luck this script can correctly guess their values.

This script has been created with ChatGPT help.

