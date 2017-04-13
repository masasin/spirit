# SPIRIT (Subimposed Past Image Records Implemented for Teleoperation)

This is my Masters research project.
I built a novel interface for the teleoperation of quadrotors, which allows the operator to have a third-person perspective of flight operations using only pose information and a monocular camera.

This implementation relies on a motion capture (mocap) setup to obtain the position and orientation, but it should work with any other methods, including but not limited to: RT-SLAM, LSD-SLAM, visual odometry, and distance sensors.
Changing the localization method would enable the system to be used outdoors.


## Table of Contents

* [Structure](#structure)
  * [Data retention](#data-retention)
* [Setup and execution](#setup-and-execution)
  * [Python](#python)
  * [Docker](#docker)
  * [LaTeX](#latex)
  * [Troubleshooting](#troubleshooting)
* [Components](#components)
  * [SPIRIT](#spirit)
  * [Data collection](#data-collection)
  * [Data analysis and visualization](#data-analysis-and-visualization)
  * [Thesis](#thesis)
* [Contribution](#contribution)
* [Licensing](#licensing)


## Structure
This repository utilizes a slightly modified version of Driven Data's [data science cookiecutter template](https://drivendata.github.io/cookiecutter-data-science/).
As a structure used by various projects, it should allow for easier reusability and sharing among groups.
It also helps with the reproducability of the data pipleine, and the collection of all pieces in one place.

### Data retention
Due to privacy requirements at Kyoto University, the data is not included in this repository.
If necessary, it may be acquired by contacting Prof Takahiro Endo at the Mechatronics Laboratory at endo@me.kyoto-u.ac.jp.


## Setup and execution

### Python
Assumptions:
* Linux operating system

The data analysis pipeline requires Python 3.6 or above.
If you don't have it on your computer, you can obtain it using `pyenv`.
It is usually best to work inside a `virtualenv` or other sandbox.
Follow the instructions for whichever system you prefer.

Once you have a virtualenv for the project, you can install the necessary packages by running the following command while in the base directory:

    pip install -r requirements.txt

### Docker
Assumptions:
* Linux operating system

Install Docker using the [official instructions](https://docs.docker.com/engine/installation/).
If you want to avoid using `sudo`, follow the instructions on the [Linux Post-installation](https://docs.docker.com/engine/installation/linux/linux-postinstall/#manage-docker-as-a-non-root-user) page.

Build by running the `build` file in the base directory, and run it using by running the `run` file.

> **Note:** In Kyoto University, building is impossible because of the KUINS proxy.
> Until Docker allows network sharing, building must happen outside the university.

Once a container has been built, you can use `docker ps` to find the currently running container, and save any new configurations using `docker commit`.
Make sure to update the `run` file to reflect the container you want to run, and (ideally) add the changes to `Dockerfile`.

Run the `join` file in order to join the currently running container.
This can be useful, for instance, for running some of the data collection or analysis programs.

If permission errors occur on files created inside the docker container (such as when commiting code), you can run the `fix_permissions` script from outside the container in order to make you the owner again.

### LaTeX

Assumptions:
* A functioning [TeXLive](https://www.tug.org/texlive) install, including XeLaTeX and latexmk.

Install the following fonts and have them accessible by TeXLive:

* Linux Libertine O
* Linux Biolinum O
* Deja Vu Sans Mono
* IPA Mincho (明朝)

Alternatively, change the font used in [`masastyle.sty`](reports/thesis/masastyle.sty#L64).

## Components
This repository contains the four main components of the project, each with its own readme.

The Jupyter notebooks in the [`notebooks`](notebooks) directory are primarily for exploration, and are included here for completeness.
They do not get updated, and may lag behind the latest changes in structure or details.

### SPIRIT
[[README]](references/readme_spirit.md)
The crux of the project.
It lives in the [`src/ros/spririt`](src/ros/spirit) directory, and contains the entire ROS portion. 

In order to run it, follow the [checklist](references/readme_spirit.md#checklist) in the SPIRIT [readme](references/readme_spirit.md).
Note that this does not attempt to gather any data, but instead enables the user to interface with the motion capture system and fly the drone.

### Data collection 
[[README]](references/readme_data.md)
The code for collecting the data is in the [`src/data`](src/data) directory.
It consists of a command line tool to record the relevant data into bagfiles, a script to convert the bagfiles into CSV for easier offline analysis, and a web interface to collect user responses to a survey and NASA-TLX results.

The experimentation phase also included video recording using OBS.
Note that, at the time of writing, there was no way to programmatically start and stop a recording session.
As such, this operation must still be done manually.

### Data analysis and visualization
[[README]](references/readme_analysis.md)
The [`src/analysis`](src/analysis) directory contains a tool to properly load and parse the generated CSV files; it is not called directly. It is also possible to perform Bayesian Estimation Supercedes the *t* test (BEST) and *t* test analysis.

The [`src/visualization`](src/visualization) directory contains [`latexify.py`](src/visualization/latexify.py), a lightweight `matplotlib` wrapper which allows easier figure generation and `.pgf` plot exporting, [`plot_tools.py`](src/visualization/plot_tools.py), which provides convenience functions for the various types of plots to be generated, and [`plot_thesis.py`](src/visualization/plot_thesis.py), which creates the actual plots.

### Thesis
[[README]](references/readme_thesis.md)
All the files for the thesis are contained in the [`reports/thesis`](reports/thesis) directory.

Before building, please run the analysis suite in order to generate the PGF plots to be included.
On first build, you need to use `make full` to generate the necessary files.
For changes in the glossary to be reflected, `make refs` needs to be run.
Otherwise, `make` is usually enough.

## Contribution
Suggested improvements and known bugs are on the [issues](https://github.com/masasin/spirit/issues/) page.
If you find something that interests you, submit your own issue, or create a pull request that I could merge.

## Licensing
* The SPIRIT software, as well as the code used for data collection and analysis, are licensed under the [MIT License](LICENSE).
* The thesis is licensed under the [Creative Commons Attribution-ShareAlike 4.0 International License](reports/thesis/LICENSE.md).

Permissions beyond the scope of these licenses are administered by Jean Nassar. Please contact jeannassar5+licensing@gmail.com for more information.

Copyright © 2017 by Jean Nassar.
