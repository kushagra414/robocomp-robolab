#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 by YOUR NAME HERE
#
#    This file is part of RoboComp
#
#    RoboComp is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RoboComp is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with RoboComp.  If not, see <http://www.gnu.org/licenses/>.
#

from genericworker import *
#import pyrealsense2 as rs
import torch
import numpy as np
import cv2
from openpifpaf.network import nets
from openpifpaf import decoder, show, transforms
import argparse
import time
import PIL
from PySide2.QtCore import QMutexLocker


COCO_IDS=["nose", "left_eye", "right_eye", "left_ear", "right_ear", "left_shoulder", "right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist", "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle" ]
SKELETON_CONNECTIONS = [("left_ankle", "left_knee"),
						("left_knee", "left_hip"),
						("right_ankle", "right_knee"),
						("right_knee", "right_hip"),
						("left_hip", "right_hip"),
						("left_shoulder", "left_hip"),
						("right_shoulder", "right_hip"),
						("left_shoulder", "right_shoulder"),
						("left_shoulder", "left_elbow"),
						("right_shoulder", "right_elbow"),
						("left_elbow", "left_wrist"),
						("right_elbow", "right_wrist"),
						("left_eye", "right_eye"),
						("nose", "left_eye"),
						("nose", "right_eye"),
						("left_eye", "left_ear"),
						("right_eye", "right_ear"),
						("left_ear", "left_shoulder"),
						("right_ear", "right_shoulder")]


class SpecificWorker(GenericWorker):
	def __init__(self, proxy_map):
		super(SpecificWorker, self).__init__(proxy_map)
		self.params = {}
		self.width = 0
		self.height = 0
		self.cameraid = 0
		self.depth = []
		self.color = []
		self.points = []
		self.openpifpaf = False
		self.viewimage = False
		self.peoplelist = []
		self.timer.timeout.connect(self.compute)
		self.Period = 1 

	def __del__(self):
		print('SpecificWorker destructor')
		#if self.pipeline:
		#	self.pipeline.stop()

	def setParams(self, params):
		self.params = params
		self.width = int(self.params["width"])
		self.height = int(self.params["height"])
		self.cameraid = int(self.params["cameraid"])
		self.openpifpaf = "true" in self.params["openpifpaf"]
		self.viewimage = "true" in self.params["viewimage"]
		# self.odepth = []
		# self.ocolor = []
		# self.opoints = []
		# self.oimgtype = []
		#cc = ColorRGB()
		#pp = PointXYZ()
		# for i in range(self.width*self.height):
		# 	self.odepth.append(0.)
		# 	self.ocolor.append(cc)
		# 	self.opoints.append(pp)
		# 	self.oimgtype.append(0.)
		# 	self.oimgtype.append(0.)
		# 	self.oimgtype.append(0.)
		self.initialize()
		self.timer.start(self.Period)
		return True
	

	def initialize(self):
		# openpifpaf configuration
		class Args:
			source = 0
			checkpoint = None
			basenet = None
			dilation = None
			dilation_end = None
			headnets = ['pif', 'paf']
			dropout = 0.0
			quad = 1
			pretrained = False
			keypoint_threshold = None
			seed_threshold = 0.2
			force_complete_pose = False
			debug_pif_indices = []
			debug_paf_indices = []
			connection_method = 'max'
			fixed_b = None
			pif_fixed_scale = None
			profile_decoder = None
			instance_threshold = 0.05
			device = torch.device(type="cpu")
			disable_cuda = False
			scale = 1
			key_point_threshold = 0.05
			head_dropout = 0.0
			head_quad = 0
			default_kernel_size = 1
			default_padding = 0
			default_dilation = 1
			head_kernel_size = 1
			head_padding = 0
			head_dilation = 0
			cross_talk = 0.0
			two_scale = False
			multi_scale = False
			multi_scale_hflip = False
			paf_th = 0.1
			pif_th = 0.1
			decoder_workers = None
			experimental_decoder = False
			extra_coupling = 0.0
		self.args = Args()
		model, _ = nets.factory_from_args(self.args)
		model = model.to(self.args.device)
		# model.cuda()
		self.processor = decoder.factory_from_args(self.args, model)
		print("hasta aqui")
		#realsense configuration
		# try:
		# 	config = rs.config()
		# 	config.enable_device(self.params["device_serial"])
		# 	config.enable_stream(rs.stream.depth, self.width, self.height, rs.format.z16, 30)
		# 	config.enable_stream(rs.stream.color, self.width, self.height, rs.format.bgr8, 30)
			
		# 	self.pointcloud = rs.pointcloud()
		# 	self.pipeline = rs.pipeline()
		# 	self.pipeline.start(config)
		# except Exception as e:
		# 	print(e)
		# 	exit(-1)

	@QtCore.Slot()
	def compute(self):
		start = time.time()
		#frames = self.pipeline.wait_for_frames()
		#if not frames:
		#	return
		
		try:
			img = self.camerargbdsimple_proxy.getImage()
			self.color = img.image
		except:
			print("Cannot read image from SimpleCameraRGBD")
			return


		self.mutex.lock()
		#self.depth = np.asanyarray(frames.get_depth_frame().get_data())
		#self.color = np.asanyarray(frames.get_color_frame().get_data())
		#self.points =  np.asanyarray(self.pointcloud.calculate(depthData).get_vertices())

		if self.openpifpaf:
			self.color = cv2.flip(self.color, 0)
			self.color = cv2.flip(self.color, 1)

			self.processImage(0.3)
			self.publishData()
			
		self.mutex.unlock()	

		if self.viewimage:
			cv2.imshow("Color frame", self.color)
			cv2.waitKey(1)
			
		print("FPS:", 1/(time.time()-start))
		return True

	def processImage(self, scale):
		image = cv2.resize(self.color, None, fx=scale, fy=scale)
		image_pil = PIL.Image.fromarray(image)
		processed_image_cpu, _, __ = transforms.EVAL_TRANSFORM(image_pil, [], None)
		processed_image = processed_image_cpu.contiguous().to(non_blocking=True)
		fields = self.processor.fields(torch.unsqueeze(processed_image, 0))[0]
		
		keypoint_sets, _ = self.processor.keypoint_sets(fields)

		self.peoplelist = []
		# create joint dictionary
		for id, p in enumerate(keypoint_sets):
			person = Person()
			person.id = id
			person.joints = dict()
			for pos, joint in enumerate(p):
				keypoint = KeyPoint()
				keypoint.i = int(joint[0] / scale)
				keypoint.j = int(joint[1] / scale)
				keypoint.score = float(joint[2])
				#keypoint.x = self.points[self.width*keypoint.j+keypoint.i][0]
				#keypoint.y = self.points[self.width*keypoint.j+keypoint.i][1]
				#keyp#oint.z = self.points[self.width*keypoint.j+keypoint.i][2]
				person.joints[COCO_IDS[pos]] = keypoint
			self.peoplelist.append(person)

			#draw
			if self.viewimage:
				for name1, name2 in SKELETON_CONNECTIONS:
					joint1 = person.joints[name1]
					joint2 = person.joints[name2]
					if joint1.score > 0.5:
						cv2.circle(self.color, (joint1.i, joint1.j), 10, (0, 0, 255))
					if joint2.score > 0.5:
						cv2.circle(self.color, (joint2.i, joint1.j), 10, (0, 0, 255))
					if joint1.score > 0.5 and joint2.score > 0.5:
						cv2.line(self.color, (joint1.i, joint1.j), (joint2.i, joint2.j), (0, 255, 0), 2)

#############################################################################
### PUBLISHER
#############################################################################
def publishData(self):
		people = PeopleData()
		people.cameraId = self.cameraid
		people.timestamp = time.time()
		people.peoplelist = self.peoplelist
		
		try:
			self.humancamerabody_proxy.newPeopleData(people)
		except:
			print("Error on camerabody data publication")
		
