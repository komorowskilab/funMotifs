# Functional Motifs

funMotifs is developed to annotate transcription factor (TF) motifs using functional annotations. The main module is src/funMotifsMain.py
Parameters to specify the input files and other parameters should be given in a configuration file. An example of such configuration file is provided in conf/main_parameters.conf

The datafiles that are specified in the main_parameters.conf have to be available for the tool to run. Please follow ReadMe files listed in the ReadMe directory to generate input datafiles and annotations for running funMotifs.
A complete set of datafiles is prodvided to re-generate the annotated motifs that are reported in the current version of funMotifsDB.

The pipeline creates a postgreSQL database and inserts the annotated motifs into a single table where each row represents a motif and the columns represent information about the motif (position, name, p-value, score) and the remaining columns are showing annotations per cell type. In order to perform this task, PostgreSQL has to be accessible on the host that is specified in the main configuration file (default is localhost). Also, the database name and login information have to be given. 

Afterwards, it can perform a logistic regression to identify functional motifs in different tissues. Finally, a variant file can be compared with those motifs to find potential harmful mutations in the motifs.

The following packages are required to run the funMotifs pipeline:
- bedtools 2.30.0
- Python 3.10.6: we recommend installing it from anaconda.com
- The following python packages are required to run the pipeline
	- pybedtools (v0.9.0): for processing the annotation data files (e.g. conda install pybedtools=0.7.8 -c bioconda)
	- psycopg2 (v2.9.3): for connecting with the PostgreSQL database (conda install -c anaconda psycopg2)

	- The following python packages are also required to run the helper modules:
		- requests
		- userlib 
		- numpy

Once the requirements above are met and the main configuration file is set correctly, run the following to start the annotation process:

cd funMotifs/src/

python3 funMotifsMain.py [-m|-r|-f|-v] --param_file='../conf/main_parameters_MM.conf' --temp_dir='tmp'

You can check python3 funMotifsMain.py -h for more information.
