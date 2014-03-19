'''
Copyright (C) 2014 ITI GmbH
All rights reserved.

This file is part of PySimulator.

PySimulator is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

PySimulator is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with PySimulator. If not, see www.gnu.org/licenses.
'''

import collections
import os

import numpy

from Plugins.SimulationResult import IntegrationResults
import PyResultX as isx

fileExtension = 'isx'
description = 'SimulationX Project File'

class Results(IntegrationResults.Results):
	""" Result Object to hold a SimulationX project file, see also
		class IntegrationResults.Results
	"""
	def __init__(self, fileName):
		IntegrationResults.Results.__init__(self)

		self.fileName = fileName

		self._name = []
		self._unit = []

		if fileName is None:
			return
		if fileName is '':
			return

		# Determine complete file name
		fullFileName = os.path.abspath(fileName)

		results = []
		model = isx.readModel(fullFileName, 'doc', results)
		doc = isx.SimXObject(model, 'doc' , None, [], results, 0)
		data = doc.LoadResult('doc.t')
		data = numpy.reshape(data, (len(data), 1))
		for result in results:
			res = doc.LoadResult(result.strIdent)
			ident = '.'.join(result.Ident[1:])
			if result.ndims == 1:
				# Scalar dimension
				self._name.append(ident)
				self._unit.append(result.Unit)
				data = numpy.c_[data, res]
			elif result.ndims == 2:
				# Vector dimension
				for i in range(1, result.Dimension[1] + 1):
					self._name.append(ident + '[' + str(i) + ']')
					self._unit.append(result.Unit)
				data = numpy.append(data, res, 1)
			elif result.ndims == 3:
				# Matrix dimension
				for i in range(1, result.Dimension[1] + 1):
					for j in range(1, result.Dimension[2] + 1):
						self._name.append(ident + '[' + str(i) + ',' + str(j) + ']')
						self._unit.append(result.Unit)
					data = numpy.append(data, res[:, i - 1, :], 1)
		model.close()
		self.timeSeries.append(IntegrationResults.TimeSeries(data[:, 0], data[:, 1:], "linear"))
		self._isParameter = len(self._name) * [False]
		self._info = len(self._name) * ['']
		self._filterUnit()

		self.nTimeSeries = len(self.timeSeries)
		self.isAvailable = True  # Shows, if there is a file available to be read

	def _filterUnit(self):

		for i in xrange(len(self._unit)):
			x = self._unit[i]
			if x == '-':
				self._unit[i] = None

	def readData(self, variableName):
		nameIndex = self._name.index(variableName)
		if nameIndex < 0:
			return None, None, None
		if self._isParameter[nameIndex]:
			y = numpy.array([self.timeSeries[1].data[0, nameIndex - self.timeSeries[0].data.shape[1]]])
			i = 1
		else:
			y = self.timeSeries[0].data[:, nameIndex]
			i = 0

		t = self.timeSeries[i].independentVariable
		method = self.timeSeries[i].interpolationMethod

		return t, y, method


	def getVariables(self):
		# Generate the dict
		variables = dict()

		# Fill the values of the dict
		for i in xrange(len(self._name)):
			name = self._name[i]

			if self._isParameter[i]:
				variability = 'fixed'
				value = self.timeSeries[1].data[0, i - self.timeSeries[0].data.shape[1]]
				seriesIndex = 1
				column = i - self.timeSeries[0].data.shape[1]
			else:
				variability = 'continuous'
				value = None
				seriesIndex = 0
				column = i
			infos = collections.OrderedDict()
			infos['Variability'] = variability
			if not self._info[i] == '':
				infos['Description'] = self._info[i]
			unit = self._unit[i]
			sign = 1

			if name in variables.keys():
				print "Same name twice " + ('(Parameter): ' if self._isParameter[i] else '(Variable): ') + name
			else:
				variables[name] = IntegrationResults.ResultVariable(value, unit, variability, infos, seriesIndex, column, sign)

		# print self._name

		return variables

	def getFileInfos(self):
		# No relevant file infos stored in a isx result file
		return dict()