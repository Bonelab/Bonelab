#---------------------------------------------------------------
# Copyright (C) 2020 Bone Imaging Laboratory
# All rights reserved.
# bonelab@ucalgary.ca
#---------------------------------------------------------------
# Created December 4, 2020
# Steven Boyd
#---------------------------------------------------------------
# Converts 4x4 transforms to/from equivalent rotation and
# translation vectors as per the Scanco Medical IPL standards.
# Typical use sets image dimensions, position and el_size_mm
# and 4x4 transform. Then call method calculateVectors() to
# compute the equivalent vectors. Dr. Bert van Rietbergen 
# provided the details on the transforms. Execute the method
# runTests() to see examples of conversions.
#---------------------------------------------------------------

import os
import sys
import vtk
import math
import numpy as np
 
class ScancoMatrixConverter():
  """A class to convert between the 4x4 matrix and the rotation and translation vectors"""
  def __init__(self, parent=None):
    
    self.image1_dim_x = 0
    self.image1_dim_y = 0
    self.image1_dim_z = 0
    self.image1_pos_x = 0
    self.image1_pos_y = 0
    self.image1_pos_z = 0
    self.image1_el_size_mm_x = 0.0820
    self.image1_el_size_mm_y = 0.0820
    self.image1_el_size_mm_z = 0.0820

    self.image2_dim_x = 0
    self.image2_dim_y = 0
    self.image2_dim_z = 0
    self.image2_pos_x = 0
    self.image2_pos_y = 0
    self.image2_pos_z = 0
    self.image2_el_size_mm_x = 0.0820
    self.image2_el_size_mm_y = 0.0820
    self.image2_el_size_mm_z = 0.0820
    
    self.Q = vtk.vtkMatrix4x4()
    
    self.rotationVector = [0, 0, 0]
    self.translationVector = [0, 0, 0]
    
  def setDimImage1(self, _dim):
    self.image1_dim_x = _dim[0]
    self.image1_dim_y = _dim[1]
    self.image1_dim_z = _dim[2]
      
  def setDimImage2(self, _dim):
    self.image2_dim_x = _dim[0]
    self.image2_dim_y = _dim[1]
    self.image2_dim_z = _dim[2]

  def setPosImage1(self, _pos):
    self.image1_pos_x = _pos[0]
    self.image1_pos_y = _pos[1]
    self.image1_pos_z = _pos[2]
      
  def setPosImage2(self, _pos):
    self.image2_pos_x = _pos[0]
    self.image2_pos_y = _pos[1]
    self.image2_pos_z = _pos[2]

  def setElSizeMMImage1(self, _el_size_mm):
    self.image1_el_size_mm_x = _el_size_mm[0]
    self.image1_el_size_mm_y = _el_size_mm[1]
    self.image1_el_size_mm_z = _el_size_mm[2]
      
  def setElSizeMMImage2(self, _el_size_mm):
    self.image2_el_size_mm_x = _el_size_mm[0]
    self.image2_el_size_mm_y = _el_size_mm[1]
    self.image2_el_size_mm_z = _el_size_mm[2]

  def setTransform(self, _Q):
    self.Q = _Q
  
  def getTransform(self):
    return self.Q
  
  def getTransformAsString(self):
    s = ""
    precision = 8
    delimiter=" "
    formatter = "{{:16.{}e}}".format(precision)
    s += "SCANCO TRANSFORMATION DATA VERSION:   10\n"
    s += "R4_MAT:\n"
    for i in range(4):
      row_data = delimiter.join([formatter.format(float(self.Q.GetElement(i,j))) for j in range(4)])
      s += " "+row_data+" \n"
    return s
  
  def getVectorsAsString(self):
    s = ""
    s += "! Rotation x:     {:16.8E}\n".format(self.rotationVector[0])
    s += "! Rotation y:     {:16.8E}\n".format(self.rotationVector[1])
    s += "! Rotation z:     {:16.8E}\n".format(self.rotationVector[2])
    s += "! Translation x:  {:16.8E}\n".format(self.translationVector[0])
    s += "! Translation y:  {:16.8E}\n".format(self.translationVector[1])
    s += "! Translation z:  {:16.8E}\n".format(self.translationVector[2])
    return s
    
  def getRotationVector(self):
    return self.rotationVector
  
  def setRotationVector(self,_vec):
    self.rotationVector[0] = _vec[0]
    self.rotationVector[1] = _vec[1]
    self.rotationVector[2] = _vec[2]
  
  def getTranslationVector(self):
    return self.translationVector
  
  def setTranslationVector(self,_vec):
    self.translationVector[0] = _vec[0]
    self.translationVector[1] = _vec[1]
    self.translationVector[2] = _vec[2]
  
  # Use this when we know matrix Q and want to find rotation and translation vectors
  def calculateVectors(self):
    Rx = vtk.vtkMatrix4x4()
    Ry = vtk.vtkMatrix4x4()
    Rz = vtk.vtkMatrix4x4()
    Tc = vtk.vtkMatrix4x4()
    Tt = vtk.vtkMatrix4x4()
    Tc_inv = vtk.vtkMatrix4x4()
    
    rot_x = math.atan2( self.Q.GetElement(2,1), self.Q.GetElement(2,2) );
    rot_y = math.atan2( -self.Q.GetElement(2,0), math.sqrt(pow(self.Q.GetElement(2,1),2) + pow(self.Q.GetElement(2,2),2)) );
    rot_z = math.atan2( self.Q.GetElement(1,0), self.Q.GetElement(0,0) );
    
    Rx.SetElement(1,1,math.cos(rot_x))
    Rx.SetElement(1,2,-math.sin(rot_x))
    Rx.SetElement(2,1,math.sin(rot_x))
    Rx.SetElement(2,2,math.cos(rot_x))

    Ry.SetElement(0,0,math.cos(rot_y))
    Ry.SetElement(0,2,math.sin(rot_y))
    Ry.SetElement(2,0,-math.sin(rot_y))
    Ry.SetElement(2,2,math.cos(rot_y))

    Rz.SetElement(0,0,math.cos(rot_z))
    Rz.SetElement(0,1,-math.sin(rot_z))
    Rz.SetElement(1,0,math.sin(rot_z))
    Rz.SetElement(1,1,math.cos(rot_z))
    
    Tc.SetElement(0,3, (self.image2_pos_x          * self.image2_el_size_mm_x) + \
                      ((self.image1_dim_x+1) * 0.5 * self.image1_el_size_mm_x))
    Tc.SetElement(1,3, (self.image2_pos_y          * self.image2_el_size_mm_y) + \
                      ((self.image1_dim_y+1) * 0.5 * self.image1_el_size_mm_y))
    Tc.SetElement(2,3, (self.image2_pos_z          * self.image2_el_size_mm_z) + \
                      ((self.image1_dim_z+1) * 0.5 * self.image1_el_size_mm_z))

    # Temporary matrices for calcuations
    T1 = vtk.vtkMatrix4x4()
    T2 = vtk.vtkMatrix4x4()
    T3 = vtk.vtkMatrix4x4()
    T4 = vtk.vtkMatrix4x4()
    T4_inv = vtk.vtkMatrix4x4()
    Ttr = vtk.vtkMatrix4x4()
    
    # Ttr=Q*inv(Tc*Rz*Ry*Rx*inv(Tc))
    vtk.vtkMatrix4x4.Invert(Tc,Tc_inv)
    vtk.vtkMatrix4x4.Multiply4x4(Rx,Tc_inv,T1)
    vtk.vtkMatrix4x4.Multiply4x4(Ry,T1,T2)
    vtk.vtkMatrix4x4.Multiply4x4(Rz,T2,T3)
    vtk.vtkMatrix4x4.Multiply4x4(Tc,T3,T4)
    vtk.vtkMatrix4x4.Invert(T4,T4_inv)
    vtk.vtkMatrix4x4.Multiply4x4(self.Q,T4_inv,Ttr)
    
    trans_x = Ttr.GetElement(0,3) - \
                                    (self.image1_pos_x * self.image1_el_size_mm_x - \
                                     self.image2_pos_x * self.image2_el_size_mm_x)
    trans_y = Ttr.GetElement(1,3) - \
                                    (self.image1_pos_y * self.image1_el_size_mm_y - \
                                     self.image2_pos_y * self.image2_el_size_mm_y)
    trans_z = Ttr.GetElement(2,3) - \
                                    (self.image1_pos_z * self.image1_el_size_mm_z - \
                                     self.image2_pos_z * self.image2_el_size_mm_z)
    
    self.rotationVector[0] = rot_x
    self.rotationVector[1] = rot_y
    self.rotationVector[2] = rot_z
    
    self.translationVector[0] = trans_x
    self.translationVector[1] = trans_y
    self.translationVector[2] = trans_z
    
    return

  # Use this when we know rotation and translation vectors and want to find matrix Q
  def calculateTransform(self):
    Rx = vtk.vtkMatrix4x4()
    Ry = vtk.vtkMatrix4x4()
    Rz = vtk.vtkMatrix4x4()
    Tc = vtk.vtkMatrix4x4()
    Tt = vtk.vtkMatrix4x4()
    Tc_inv = vtk.vtkMatrix4x4()
    
    rot_x = self.rotationVector[0]
    rot_y = self.rotationVector[1]
    rot_z = self.rotationVector[2]
    trans_x = self.translationVector[0]
    trans_y = self.translationVector[1]
    trans_z = self.translationVector[2]
    
    Rx.SetElement(1,1,math.cos(rot_x))
    Rx.SetElement(1,2,-math.sin(rot_x))
    Rx.SetElement(2,1,math.sin(rot_x))
    Rx.SetElement(2,2,math.cos(rot_x))

    Ry.SetElement(0,0,math.cos(rot_y))
    Ry.SetElement(0,2,math.sin(rot_y))
    Ry.SetElement(2,0,-math.sin(rot_y))
    Ry.SetElement(2,2,math.cos(rot_y))

    Rz.SetElement(0,0,math.cos(rot_z))
    Rz.SetElement(0,1,-math.sin(rot_z))
    Rz.SetElement(1,0,math.sin(rot_z))
    Rz.SetElement(1,1,math.cos(rot_z))
    
    Tc.SetElement(0,3, (self.image2_pos_x          * self.image2_el_size_mm_x) + \
                      ((self.image1_dim_x+1) * 0.5 * self.image1_el_size_mm_x))
    Tc.SetElement(1,3, (self.image2_pos_y          * self.image2_el_size_mm_y) + \
                      ((self.image1_dim_y+1) * 0.5 * self.image1_el_size_mm_y))
    Tc.SetElement(2,3, (self.image2_pos_z          * self.image2_el_size_mm_z) + \
                      ((self.image1_dim_z+1) * 0.5 * self.image1_el_size_mm_z))

    Tt.SetElement(0,3, trans_x + \
                        (self.image1_pos_x * self.image1_el_size_mm_x) - \
                        (self.image2_pos_x * self.image2_el_size_mm_x))
    Tt.SetElement(1,3, trans_y + \
                        (self.image1_pos_y * self.image1_el_size_mm_y) - \
                        (self.image2_pos_y * self.image2_el_size_mm_y))
    Tt.SetElement(2,3, trans_z + \
                        (self.image1_pos_z * self.image1_el_size_mm_z) - \
                        (self.image2_pos_z * self.image2_el_size_mm_z))
    
    # Temporary matrices for calcuations
    T1 = vtk.vtkMatrix4x4()
    T2 = vtk.vtkMatrix4x4()
    T3 = vtk.vtkMatrix4x4()
    T4 = vtk.vtkMatrix4x4()
    T4_inv = vtk.vtkMatrix4x4()
    Ttr = vtk.vtkMatrix4x4()
    
    # Q=Tt*Tc*Rz*Ry*Rx*inv(Tc)
    vtk.vtkMatrix4x4.Invert(Tc,Tc_inv)
    vtk.vtkMatrix4x4.Multiply4x4(Rx,Tc_inv,T1)
    vtk.vtkMatrix4x4.Multiply4x4(Ry,T1,T2)
    vtk.vtkMatrix4x4.Multiply4x4(Rz,T2,T3)
    vtk.vtkMatrix4x4.Multiply4x4(Tc,T3,T4)
    vtk.vtkMatrix4x4.Multiply4x4(Tt,T4,self.Q)
    
    return
    
  def runTests(self):
    
    print("!---------------------------------------------------------------")
    print("! Test 1: Find the vectors given the transform")
    print("!---------------------------------------------------------------")
    self.setDimImage1([326, 310, 660])
    self.setDimImage2([441, 436, 668])
    self.setPosImage1([587, 648, -158])
    self.setPosImage2([250, 583, -169])
    self.setElSizeMMImage1([0.082, 0.082, 0.082])
    self.setElSizeMMImage2([0.082, 0.082, 0.082])
    mat = vtk.vtkMatrix4x4()
    mat.SetElement(0,0,4.9049170E-01)
    mat.SetElement(0,1,8.7141793E-01)
    mat.SetElement(0,2,-6.9776085E-03)
    mat.SetElement(0,3,-1.4565407E+01)
    mat.SetElement(1,0,-8.7128357E-01)
    mat.SetElement(1,1,4.9053916E-01)
    mat.SetElement(1,2,1.5371266E-02)
    mat.SetElement(1,3,6.7224909E+01)
    mat.SetElement(2,0,1.6817587E-02)
    mat.SetElement(2,1,-1.4600026E-03)
    mat.SetElement(2,2,9.9985751E-01)
    mat.SetElement(2,3,2.7510843E-02)
    self.setTransform(mat)
    self.calculateVectors()
    print("! Input --------------------------------------------------------\n")
    print(self.getTransformAsString())
    print("! Output -------------------------------------------------------\n")
    print(self.getVectorsAsString())
    print("! Expected output ----------------------------------------------\n")
    self.setRotationVector([-1.4602E-03, -1.6818E-02, -1.0581E+00])
    self.setTranslationVector([-6.7973E+00, 1.7044E+00, -3.9456E-01])
    print(self.getVectorsAsString())
    
    print("!---------------------------------------------------------------")
    print("! Test 2: Find the vectors given the transform")
    print("!---------------------------------------------------------------")
    self.setDimImage1([430, 560, 168])
    self.setDimImage2([420, 580, 168])
    self.setPosImage1([778, 502, 0])
    self.setPosImage2([738, 537, 0])
    self.setElSizeMMImage1([0.0607, 0.0607, 0.0607])
    self.setElSizeMMImage2([0.0607, 0.0607, 0.0607])
    mat = vtk.vtkMatrix4x4()
    mat.SetElement(0,0,9.9979899E-01)
    mat.SetElement(0,1,-1.6913449E-04)
    mat.SetElement(0,2,-2.0048670E-02)
    mat.SetElement(0,3,2.2340977E+00)
    mat.SetElement(1,0,1.4309149E-03)
    mat.SetElement(1,1,9.9801640E-01)
    mat.SetElement(1,2,6.2938250E-02)
    mat.SetElement(1,3,-1.9364735E+00)
    mat.SetElement(2,0,1.9998257E-02)
    mat.SetElement(2,1,-6.2954287E-02)
    mat.SetElement(2,2,9.9781603E-01)
    mat.SetElement(2,3,1.6841473E+00)
    self.setTransform(mat)
    self.calculateVectors()
    print("! Input --------------------------------------------------------\n")
    print(self.getTransformAsString())
    print("! Output -------------------------------------------------------\n")
    print(self.getVectorsAsString())
    print("! Expected output ----------------------------------------------\n")
    self.setRotationVector([-6.3009E-02, -2.0000E-02, 1.4312E-03])
    self.setTranslationVector([-3.1674E-01, 4.9520E-01, -2.9353E-01])
    print(self.getVectorsAsString())
    
    print("!---------------------------------------------------------------")
    print("! Test 3: Find the transform given the vectors")
    print("!---------------------------------------------------------------")
    self.setDimImage1([255, 341, 110])
    self.setDimImage2([271, 342, 110])
    self.setPosImage1([588, 547, 0])
    self.setPosImage2([612, 529, 0])
    self.setElSizeMMImage1([0.082, 0.082, 0.082])
    self.setElSizeMMImage2([0.082, 0.082, 0.082])
    self.setRotationVector([-0.025520, -0.0041147, -0.32443])
    self.setTranslationVector([-0.50908, -0.73686, -0.66945])
    self.calculateTransform()
    print("! Input --------------------------------------------------------\n")
    print(self.getVectorsAsString())
    print("! Output -------------------------------------------------------\n")
    print(self.getTransformAsString())
    print("! Expected output ----------------------------------------------\n")
    mat = vtk.vtkMatrix4x4()
    mat.SetElement(0,0,9.47824555e-01)
    mat.SetElement(0,1,3.18764295e-01)
    mat.SetElement(0,2,4.23532522e-03)
    mat.SetElement(0,3,-1.76274195e+01)
    mat.SetElement(1,0,-3.18765875e-01)
    mat.SetElement(1,1,9.47490478e-01)
    mat.SetElement(1,2,2.54972682e-02)
    mat.SetElement(1,3,2.29798617e+01)
    mat.SetElement(2,0,4.11468839e-03)
    mat.SetElement(2,1,-2.55170140e-02)
    mat.SetElement(2,2,9.99665920e-01)
    mat.SetElement(2,3,5.47067711e-01)
    self.setTransform(mat)
    print(self.getTransformAsString())
    
    print("!---------------------------------------------------------------")
    print("! Test 4: Find the vectors given the transform")
    print("!---------------------------------------------------------------")
    self.setDimImage1([255, 341, 110])
    self.setDimImage2([271, 342, 110])
    self.setPosImage1([588, 547, 0])
    self.setPosImage2([612, 529, 0])
    self.setElSizeMMImage1([0.082, 0.082, 0.082])
    self.setElSizeMMImage2([0.082, 0.082, 0.082])
    mat = vtk.vtkMatrix4x4()
    mat.SetElement(0,0,9.47824555e-01)
    mat.SetElement(0,1,3.18764295e-01)
    mat.SetElement(0,2,4.23532522e-03)
    mat.SetElement(0,3,-1.76274195e+01)
    mat.SetElement(1,0,-3.18765875e-01)
    mat.SetElement(1,1,9.47490478e-01)
    mat.SetElement(1,2,2.54972682e-02)
    mat.SetElement(1,3,2.29798617e+01)
    mat.SetElement(2,0,4.11468839e-03)
    mat.SetElement(2,1,-2.55170140e-02)
    mat.SetElement(2,2,9.99665920e-01)
    mat.SetElement(2,3,5.47067711e-01)
    self.setTransform(mat)
    self.calculateVectors()
    print("! Input --------------------------------------------------------\n")
    print(self.getTransformAsString())
    print("! Output -------------------------------------------------------\n")
    print(self.getVectorsAsString())
    print("! Expected output ----------------------------------------------\n")
    self.setRotationVector([-0.025520, -0.0041147, -0.32443])
    self.setTranslationVector([-0.50908, -0.73686, -0.66945])
    print(self.getVectorsAsString())
    
    
#---------------------------------------------------------------
#---------------------------------------------------------------
#  Provided by Bert van Rietbergen
#     
#  % Image 1 has the following geometry:
#  pos1_x= 588;
#  pos1_y= 547;
#  pos1_z= 0;
#  dim1_x= 255;
#  dim1_y= 341;
#  dim1_z= 110;
#  el_size_mm1_x= 0.082;
#  el_size_mm1_y= 0.082;
#  el_size_mm1_z= 0.082;
# 
#  % Image 2 has the following geometry:
#  pos2_x= 612;
#  pos2_y= 529;
#  pos2_z= 0;
#  dim2_x= 271;
#  dim2_y= 342;
#  dim2_z= 110;
#  el_size_mm2_x= 0.082;
#  el_size_mm2_y= 0.082;
#  el_size_mm2_z= 0.082;
# 
#  % The 3 spatial rotations as printed to the screen are:
#  A_x = -0.025520;
#  A_y = -0.0041147;
#  A_z = -0.32443;
# 
#  % The translation in the 3 spatial directions as printed to the screen are:
#  T_x= -0.50908;
#  T_y= -0.73686;
#  T_z= -0.66945;
# 
#  % During registration, the position of the images is not accounted for
#  % (set to zero). The transformation matrix, however, should also work for 
#  % other subsets of the same image2. Therefore, we need to specify the 
#  % translations relative to the ISQ origin.
#  % During registration, the center of rotation was (dim1+1)/2 * el_size_mm
#  % After accounting for pos2, this same point in image 2 becomes:
#  C_x= pos2_x*el_size_mm2_x + ((dim1_x+1)*0.5)*el_size_mm1_x;
#  C_y= pos2_y*el_size_mm2_y + ((dim1_y+1)*0.5)*el_size_mm1_y;
#  C_z= pos2_z*el_size_mm2_z + ((dim1_z+1)*0.5)*el_size_mm1_z;
# 
#  % The rotated image2 then is the same as during registration, but shifted
#  % by a vector pos2-pos1. We thus need to apply an additional translation
#  % to correct for this:
#  T_x= T_x + (pos1_x*el_size_mm1_x - pos2_x*el_size_mm2_x);
#  T_y= T_y + (pos1_y*el_size_mm1_y - pos2_y*el_size_mm2_y);
#  T_z= T_z + (pos1_z*el_size_mm1_z - pos2_z*el_size_mm2_z);
# 
#  % Then the submatrices can be calculated as:
#  Rx= [   1         0         0        0
#          0       cos(A_x) -sin(A_x)   0
#          0       sin(A_x)  cos(A_x)  0
#          0         0         0        1];
# 
#  Ry= [ cos(A_y)    0       sin(A_y)   0
#          0         1         0        0
#       -sin(A_y)    0       cos(A_y)   0
#          0         0         0        1];
# 
#  Rz= [ cos(A_z) -sin(A_z)    0        0
#        sin(A_z)  cos(A_z)    0        0
#          0        0          1        0
#          0        0          0        1];
#     
#  Tc= [ 1 0 0 C_x
#        0 1 0 C_y
#        0 0 1 C_z
#        0 0 0 1 ];
# 
#  Tt= [ 1 0 0 T_x
#        0 1 0 T_y
#        0 0 1 T_z
#        0 0 0 1 ];
# 
#  % And the total transformation matrix as written to the Tmat.dat file is:
# 
#  Q=Tt*Tc*Rz*Ry*Rx*inv(Tc)
# 
#  % =========================================================
#  % Suppose that you have this matrix and want to recover the 
#  % translations, you can do so by calculating:
#  % =========================================================
# 
#  Ttr=Q*inv(Tc*Rz*Ry*Rx*inv(Tc))
# 
#  % But this needs to be corrected again, to give the translations:
#  Tr_x= Ttr(1,4) - (pos1_x*el_size_mm1_x - pos2_x*el_size_mm2_x)
#  Tr_y= Ttr(2,4) - (pos1_y*el_size_mm1_y - pos2_y*el_size_mm2_y)
#  Tr_z= Ttr(3,4) - (pos1_z*el_size_mm1_z - pos2_z*el_size_mm2_z)
#---------------------------------------------------------------
#---------------------------------------------------------------
