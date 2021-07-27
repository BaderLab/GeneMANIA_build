#!/bin/bash
#
# This file is part of GeneMANIA.
# Copyright (C) 2010 University of Toronto.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#

#
# run a dbutil python module
#
# this just sets the path and passes
# the args on through. First arg must 
# be the module name, with the .py 
# extension removed.
#
# eg:
#  
#    ./run.sh cb some/path/to/db.cfg module_args ...
#

MYSQL=mysql
MVN=mvn
PYTHON=python

PYTHONPATH=src/main/python/dbutil:src/main/python/dbstats:$PYTHONPATH $PYTHON -m $@
