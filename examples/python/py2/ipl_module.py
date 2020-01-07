import sys
import argparse
import vtk
import vtkn88
import time



#===============================================
# IPL functions
#===============================================

# /add_aims
#===============================================

def ipl_add_aims_settings():
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/add_aims"
    print "  -%-26s%s" % ("input1","in")
    print "  -%-26s%s" % ("input2","in1")
    print "  -%-26s%s" % ("output","out")
    print "!-------------------------------------------------------------------------"

def ipl_add_aims( image_in1, image_in2 ):
		ipl_add_aims_settings()
		
		extent1 = image_in1.GetExtent()
		
		voi1 = vtk.vtkExtractVOI()
		voi1.SetInput(image_in1)
		voi1.SetVOI( extent1[0], extent1[1], 
            		 extent1[2], extent1[3], 
            		 extent1[4], extent1[5] )
            		
		extent2 = image_in2.GetExtent()
		
		voi2 = vtk.vtkExtractVOI()
		voi2.SetInput(image_in2)
		voi2.SetVOI( extent2[0], extent2[1], 
            		 extent2[2], extent2[3], 
            		 extent2[4], extent2[5] )
            		
		shift1 = vtk.vtkImageShiftScale()
		shift1.SetInputConnection(voi1.GetOutputPort())
		shift1.SetOutputScalarTypeToChar()
		shift1.Update()

		shift2 = vtk.vtkImageShiftScale()
		shift2.SetInputConnection(voi2.GetOutputPort())
		shift2.SetOutputScalarTypeToChar()
		shift2.Update()

		add = vtk.vtkImageMathematics()
		add.SetInput1(shift1.GetOutput())
		add.SetInput2(shift2.GetOutput())
		add.SetOperationToAdd()
		add.Update()

		temp = vtk.vtkImageMathematics()
		temp.SetInput1(add.GetOutput())
		temp.SetConstantC(-2)
		temp.SetConstantK(127)
		temp.SetOperationToReplaceCByK()
		temp.Update()
	
		image_out = temp.GetOutput()
		return image_out

# /bounding_box_cut
#===============================================

def ipl_bounding_box_cut_settings(border):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/bounding_box_cut"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%s" % ("output","out")
    print "  -%-26s%s" % ("z_only", "false" )
    print "  -%-26s%d %d %d" % ("border", border[0], border[1], border[2])
    print "!-------------------------------------------------------------------------"

def ipl_bounding_box_cut( image_in,  border ):
		ipl_bounding_box_cut_settings(border)
		extent = image_in.GetExtent()	
		box = vtk.vtkImageReslice()
		box.SetInput( image_in )
		box.SetOutputExtent(extent[0]-border[0], extent[1]+border[0], 
    	                    extent[2]-border[1], extent[3]+border[1], 
     	                    extent[4]-border[2], extent[5]+border[2])
		box.Update()
	
		image_out = box.GetOutput()
		return image_out

# /cl_rank_extract
#===============================================

def ipl_cl_rank_extract_settings(first_rank,last_rank):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/cl_rank_extract"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%s" % ("first_rank",first_rank)
    print "  -%-26s%s" % ("last_rank",last_rank)
    print "  -%-26s%s" % ("connect_boundary","false")
    print "  -%-26s%d" % ("value_in_range ",127)
    print "!-------------------------------------------------------------------------"
    
def ipl_cl_rank_extract( image_in,  first_rank, last_rank ):
		ipl_cl_rank_extract_settings(first_rank,last_rank)
		step1 = image_in
		temp = vtk.vtkImageMathematics()
		temp.SetInput1(image_in)
		temp.SetConstantC(127)
		temp.SetConstantK(0)
		temp.SetOperationToReplaceCByK()

		for x in range(first_rank,last_rank+1):

			connect = vtkn88.vtkn88ImageConnectivityFilter()
			connect.SetInput(image_in)
			connect.SetExtractionModeToLargestRegion()
			connect.Update()
		
			sub = vtk.vtkImageMathematics()
			sub.SetInput1(image_in)
			sub.SetInput2(connect.GetOutput())
			sub.SetOperationToSubtract()
			sub.Update()
		
			add = vtk.vtkImageMathematics()
			add.SetInput1(temp.GetOutput())
			add.SetInput2(connect.GetOutput())
			add.SetOperationToAdd()
			add.Update()

			temp = add
			
			image_in = sub.GetOutput()
		
		image_out = temp.GetOutput()
		return image_out

# /cl_slicewise_extract
#===============================================

def ipl_cl_slicewise_extract_settings(lower, upper, value_in):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/cl_slicewise_extractow"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%.5f" % ("lo_vol_fract_in_perc",lower)
    print "  -%-26s%.5f" % ("up_vol_fract_in_perc",upper)
    print "  -%-26s%d" % ("value_in_range", value_in)
    print "!-------------------------------------------------------------------------"
    
def ipl_cl_slicewise_extract(image_in, lower, upper, value_in):

		ipl_cl_slicewise_extract_settings(lower, upper, value_in)  
		connect = vtkn88.vtkn88ImageConnectivityFilter()
		connect.SetInput(image_in)
		connect.SetExtractionModeToLargestRegion()
		connect.Update()
	
		image_out = connect.GetOutput()
		return image_out

# /dilation
#===============================================

def ipl_dilation_settings(dilate, boundary):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/dilation"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%s" % ("output","out")
    print "  -%-26s%s" % ("dilate_distance",dilate)
    print "  -%-26s%d %d %d" % ("continuous_at_boundary",boundary[0], boundary[1], boundary[2] )
    print "  -%-26s%s" % ("use_previous_margin","false")
    print "!-------------------------------------------------------------------------"
    
def ipl_dilation(image_in, dilate_distance, boundary):
		ipl_dilation_settings(dilate_distance, boundary)   
		extent = image_in.GetExtent()

		#Actual distance of pixel dilation
		distance = dilate_distance + 1
	
		pad = vtk.vtkImageReslice()
		pad.SetInput(image_in)
		pad.SetOutputExtent(extent[0]-distance-1, extent[1]+distance+1, 
    	               	    extent[2]-distance-1, extent[3]+distance+1, 
   	                	    extent[4]-distance-1, extent[5]+distance+1)
		pad.Update()

		#Kernel size is twice the dilation distance plus one for the center voxel

		dilate = vtk.vtkImageContinuousDilate3D()
		dilate.SetInputConnection(pad.GetOutputPort())
		dilate.SetKernelSize(2*distance+1,2*distance+1,2*distance+1)
		dilate.Update()

		ext = dilate.GetOutput().GetExtent()

		border = vtk.vtkExtractVOI()
		border.SetInput(dilate.GetOutput())
		border.SetVOI( ext[0]+boundary[0]*distance, ext[1]-boundary[0]*distance, 
   	   	               ext[2]+boundary[1]*distance, ext[3]-boundary[1]*distance, 
   		               ext[4]+boundary[2]*distance, ext[5]-boundary[2]*distance)
		border.Update()

		clip = vtk.vtkImageReslice()
		clip.SetInput(border.GetOutput())
		clip.SetOutputExtent( ext[0]+1, ext[1]-1, 
    	            		  ext[2]+1, ext[3]-1, 
   	                          ext[4]+1, ext[5]-1)
		clip.MirrorOn()                
		clip.Update()
	
		image_out = clip.GetOutput()
		return image_out
	
# /erosion
#===============================================

def ipl_erosion_settings(erode):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/erosion"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%s" % ("output","out")
    print "  -%-26s%s" % ("erode_distance",erode)
    print "  -%-26s%s" % ("use_previous_margin","false")
    print "!-------------------------------------------------------------------------"

def ipl_erosion(image_in, erode_distance):    
		ipl_erosion_settings(erode_distance)
		extent = image_in.GetExtent()

		#Actual distance of pixel erosion
		distance = erode_distance + 1

		pad = vtk.vtkImageReslice()
		pad.SetInput(image_in)
		pad.SetOutputExtent(extent[0], extent[1], 
    	               	    extent[2], extent[3], 
   	                	    extent[4], extent[5])
		pad.Update()

		#Kernel size is twice the dilation distance plus one for the center voxel
		erode = vtk.vtkImageContinuousErode3D()
		erode.SetInputConnection(pad.GetOutputPort())
		erode.SetKernelSize(2*distance+1,2*distance+1,2*distance+1)
		erode.Update()
		
		voi = vtk.vtkExtractVOI()
		voi.SetInput(erode.GetOutput())
		voi.SetVOI(extent[0]+distance, extent[1]-distance, 
 	 	           extent[2]+distance, extent[3]-distance, 
	               extent[4]+distance, extent[5]-distance)
		voi.Update()
		
		image_out = voi.GetOutput()
		return image_out

# /gauss_lp
#===============================================

def ipl_gauss_lp_settings(sigma,support):
    print "!-------------------------------------------------------------------------"
    print "/gauss_lp"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%s" % ("output","gauss")
    print "  -%-26s%.5f" % ("sigma",sigma)
    print "  -%-26s%d" % ("support",support)
    print "!-------------------------------------------------------------------------"
	
def ipl_gauss_lp( image_in,  sigma, support ):
        ipl_gauss_lp_settings(sigma,support)
        gauss = vtk.vtkImageGaussianSmooth()
        gauss.SetInput(image_in)
        gauss.SetDimensionality(3)
        gauss.SetStandardDeviation( sigma ) 
        gauss.SetRadiusFactors( support, support, support )
        gauss.Update()
        
        extent = gauss.GetOutput().GetExtent()
        off = [support, support, support]
        voi = vtk.vtkExtractVOI()
        voi.SetInput(gauss.GetOutput())
        voi.SetVOI( extent[0]+off[0], extent[1]-off[0], 
                    extent[2]+off[1], extent[3]-off[1], 
                    extent[4]+off[2], extent[5]-off[2] )
        voi.Update()
        
        image_out = voi.GetOutput()
        return image_out

# /maskaimpeel
#===============================================

def ipl_maskaimpeel_settings(peel_iter):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/maskaimpeel"
    print "  -%-26s%s" % ("input_output","in")
    print "  -%-26s%s" % ("filename","in1")
    print "  -%-26s%d" % ("peel_iter",peel_iter)
    print "!-------------------------------------------------------------------------"
    
def ipl_maskaimpeel( image_in1, image_in2, peel_iter ):
		ipl_maskaimpeel_settings(peel_iter)
		
		extent = image_in1.GetExtent()
		
		voi = vtk.vtkExtractVOI()
		voi.SetInput(image_in1)
		voi.SetVOI( extent[0], extent[1], 
            		extent[2], extent[3], 
            		extent[4], extent[5] )
		voi.Update()
		
		shift = vtk.vtkImageShiftScale()
		shift.SetInputConnection(voi.GetOutputPort())
		shift.SetOutputScalarTypeToUnsignedChar()
		shift.Update()

		mask = vtk.vtkImageMask()
		mask.SetImageInput(image_in2)
		mask.SetMaskInput(shift.GetOutput())
		mask.SetMaskedOutputValue(0)
		mask.Update()
	
		if peel_iter != 0:
			erode = vtk.vtkImageContinuousErode3D()
			erode.SetInputConnection(mask.GetOutputPort())
			erode.SetKernelSize(peel_iter+1,peel_iter+1,peel_iter+1)
			erode.Update()
			
			mask = erode
			
		image_out = mask.GetOutput()
		return image_out

# /median_filter
#===============================================

def ipl_median_filter_settings(support):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/median_filter"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%s" % ("output","out")
    print "  -%-26s%d" % ("support",support)
    print "!-------------------------------------------------------------------------"
    
def ipl_median_filter( image_in, support ):
	ipl_median_filter_settings(support)
	
	extent = image_in.GetExtent()

	voi = vtk.vtkExtractVOI()
	voi.SetInput(image_in)
	voi.SetVOI( extent[0]+support, extent[1]-support, 
            	extent[2]+support, extent[3]-support, 
           	 	extent[4]+support, extent[5]-support)
	voi.Update()

	median = vtk.vtkImageMedian3D( )
	median.SetKernelSize ( support, support, support )
	median.SetInputConnection(voi.GetOutputPort())
	median.Update()

	image_out = median.GetOutput()
	return image_out

# /open
#===============================================

def ipl_open_settings(open):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/open"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%s" % ("output","out")
    print "  -%-26s%s" % ("open_distance",open)
    print "!-------------------------------------------------------------------------"

def ipl_open( image_in, open ):
		ipl_open_settings(open)
		extent = image_in.GetExtent()	

		clip = vtk.vtkImageReslice()
		clip.SetInput(image_in)
		clip.SetOutputExtent(extent[0]-open-2, extent[1]+open+2, 
                     		 extent[2]-open-2, extent[3]+open+2, 
                     		 extent[4]-open-2, extent[5]+open+2)
		clip.MirrorOn()
		clip.Update()

		erode = vtk.vtkImageContinuousErode3D()
		erode.SetInputConnection(clip.GetOutputPort())
		erode.SetKernelSize(2*open+1,2*open+1,2*open+1)
		erode.Update()

		#Kernel size is twice the dilation distance plus one for the center voxel

		dilate = vtk.vtkImageContinuousDilate3D()
		dilate.SetInputConnection(erode.GetOutputPort())
		dilate.SetKernelSize(2*open+1,2*open+1,2*open+1)
		dilate.Update()

		voi = vtk.vtkExtractVOI()
		voi.SetInput(dilate.GetOutput())
		voi.SetVOI( extent[0], extent[1], 
    	            extent[2], extent[3], 
   	                extent[4], extent[5])
		voi.Update()

		image_out = voi.GetOutput()
		return image_out

# /read
#===============================================
 
def ipl_read_settings(input):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/read"
    print "  -%-26s%s" % ("name","in")
    print "  -%-26s%s" % ("filename",input)
    print "!-------------------------------------------------------------------------"

def ipl_read(input):
		
		ipl_read_settings(input)
		
		print "Reading: ", input
		reader = vtkn88.vtkn88AIMReader()
		reader.SetFileName(input)
		reader.GlobalWarningDisplayOff()
		reader.Update()
		
		image_in = reader.GetOutput()
		return image_in
# /seg_gauss
#===============================================

def ipl_seg_gauss_settings(sigma,support,lower,upper,value_in_range):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/seg_gauss"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%s" % ("output","gauss")
    print "  -%-26s%.5f" % ("sigma",sigma)
    print "  -%-26s%d" % ("support",support)
    print "  -%-26s%.5f" % ("lower_in_perm_aut_al",lower)
    print "  -%-26s%.5f" % ("upper_in_perm_aut_al",upper)
    print "  -%-26s%d" % ("value_in_range",value_in_range)
    print "  -%-26s%d" % ("unit",0)
    print "!-------------------------------------------------------------------------"
    
def ipl_seg_gauss( image_in, sigma, support, lower, upper, value_in_range ):
		ipl_seg_gauss_settings(sigma,support,lower,upper,value_in_range)
	
		gauss = vtk.vtkImageGaussianSmooth()
		gauss.SetInputConnection(image_in())
		gauss.SetDimensionality(3)
		gauss.SetStandardDeviation( sigma ) 
		gauss.SetRadiusFactors( support, support, support )
		gauss.Update()

		# If there is an offset in the input file, we scrub 
		# those layers from the image data (as does IPL during
		# the thresholding function

		extent = reader.GetOutput().GetExtent()

		voi = vtk.vtkExtractVOI()
		voi.SetInputConnection(gauss.GetOutputPort())
		voi.SetVOI( extent[0]+support, extent[1]-support, 
    	     	    extent[2]+support, extent[3]-support, 
    	        	extent[4]+support, extent[5]-support)
		voi.Update()

		# Scale the thresholds from 'per 1000' of maximum scalar value
		max_scaler = gauss.GetOutput().GetScalarTypeMax()

		scaled_lower = lower / 1000.0 * max_scaler
		scaled_upper = upper / 1000.0 * max_scaler

		thres = vtk.vtkImageThreshold()
		thres.SetInputConnection(voi.GetOutputPort())
		thres.ThresholdBetween(scaled_lower, scaled_upper)
		thres.SetInValue( value_in_range ) 
		thres.SetOutValue( 0 ) 
		thres.SetOutputScalarTypeToChar()
		thres.Update()
	
		image_out = thres.GetOutput()
		return image_out
	
# /set_value
#===============================================

def ipl_set_value_settings(object, background):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/set_value"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%s" % ("value_object",object)
    print "  -%-26s%s" % ("value_background",background)
    print "!-------------------------------------------------------------------------"

def ipl_set_value(image_in, object, background):
		ipl_set_value_settings(object, background)	
		temp = reader

		if object == 0 and background == 127:
			invert = vtk.vtkImageMathematics()
			invert.SetInput1(image_in)
			invert.SetOperationToInvert()
			invert.Update()
	
			set_back = vtk.vtkImageMathematics()
			set_back.SetInput1(invert.GetOutput())
			set_back.SetConstantC(32767)
			set_back.SetConstantK(127)
			set_back.SetOperationToReplaceCByK()
			set_back.Update()
	
			temp = set_back
	
		elif object == 0:
			set_back = vtk.vtkImageMathematics()
			set_back.SetInput1(image_in)
			set_back.SetConstantC(0)
			set_back.SetConstantK(background)
			set_back.SetOperationToReplaceCByK()

			set_obj = vtk.vtkImageMathematics()
			set_obj.SetInput1(set_back.GetOutput())
			set_obj.SetConstantC(127)
			set_obj.SetConstantK(object)
			set_obj.SetOperationToReplaceCByK()
			set_obj.Update()
			
			temp = set_obj

		else:
			set_obj = vtk.vtkImageMathematics()
			set_obj.SetInput1(image_in)
			set_obj.SetConstantC(127)
			set_obj.SetConstantK(object)
			set_obj.SetOperationToReplaceCByK()
	
			set_back = vtk.vtkImageMathematics()
			set_back.SetInput1(set_obj.GetOutput())
			set_back.SetConstantC(0)
			set_back.SetConstantK(background)
			set_back.SetOperationToReplaceCByK()
			set_back.Update()
			
			temp = set_back 
			
		image_out = temp.GetOutput()
		return image_out

# /threshold
#===============================================

def ipl_threshold_settings(lower,upper,value_in_range):
    print "!-------------------------------------------------------------------------"
    print "/threshold"
    print "  -%-26s%s" % ("input","gauss")
    print "  -%-26s%s" % ("output","seg")
    print "  -%-26s%.5f" % ("lower_in_perm_aut_al",lower)
    print "  -%-26s%.5f" % ("upper_in_perm_aut_al",upper)
    print "  -%-26s%d" % ("value_in_range",value_in_range)
    print "  -%-26s%d" % ("unit",0)
    print "!-------------------------------------------------------------------------"

def ipl_threshold( image_in, lower, upper, value_in_range ):
        ipl_threshold_settings( lower, upper, value_in_range )
        max_scaler = image_in.GetScalarTypeMax()
        scaled_lower = lower / 1000.0 * max_scaler
        scaled_upper = upper / 1000.0 * max_scaler
        
        thres = vtk.vtkImageThreshold()
        thres.SetInput(image_in)
        thres.ThresholdBetween(scaled_lower, scaled_upper)
        thres.SetInValue( value_in_range ) 
        thres.SetOutValue( 0  )
        #thres.SetOutputScalarTypeToSignedChar()
        thres.Update()
        image_out = thres.GetOutput()
        return image_out
        
# /write
#===============================================
 
def ipl_write_settings(input, output):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/write"
    print "  -%-26s%s" % ("name","in")
    print "  -%-26s%s" % ("filename",output)
    print "!-------------------------------------------------------------------------"
    
def ipl_write( image_in, output):
		ipl_write_settings(image_in, output)
		print "Writing: ", output
		extent = image_in.GetExtent()
		
		voi = vtk.vtkExtractVOI()
		voi.SetInput(image_in)
		voi.SetVOI( extent[0], extent[1], 
            		extent[2], extent[3], 
            		extent[4], extent[5] )
		  
		writer = vtkn88.vtkn88AIMWriter()
		writer.SetInputConnection(voi.GetOutputPort())
		writer.SetFileName(output)
		writer.Update()
		
		print "Done"
#===============================================
# Non IPL functions
#===============================================

# examine_geometry
#===============================================
        
def ipl_examine_geometry( image_in ):
    im = image_in
    print "!-------------------------------------------------------------------------"
    print "  %-26s%8d %8d %8d" %("dim",im.GetDimensions()[0],im.GetDimensions()[1],im.GetDimensions()[2])
    print "  %-26s%8d %8d %8d" %("off",reader.GetOffset()[0],reader.GetOffset()[1],reader.GetOffset()[2])
    print "  %-26s%8d %8d %8d" %("pos",reader.GetPosition()[0],reader.GetPosition()[1],reader.GetPosition()[2])
    print "  %-26s%8.4f %8.4f %8.4f" % ("element size in mm",im.GetSpacing()[0],im.GetSpacing()[1],im.GetSpacing()[2])
    print "  %-26s%8.4f %8.4f %8.4f" % ("phys dim in mm",im.GetSpacing()[0]*im.GetDimensions()[0],
                                                         im.GetSpacing()[1]*im.GetDimensions()[1],
                                                         im.GetSpacing()[2]*im.GetDimensions()[2])
    print "  %-26s%s" % ("Type of data",im.GetScalarTypeAsString())
    print "!-------------------------------------------------------------------------"

# /add_offset_mirror
#===============================================

def ipl_add_offset_mirror_settings(offset):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/filloffset_mirror"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%d %d %d" % ("add_offset",offset[0], offset[1], offset[2] )
    print "!-------------------------------------------------------------------------"
    
def ipl_add_offset_mirror(image_in, offset):
		ipl_add_offset_mirror_settings(offset)
		extent = image_in.GetExtent()
	
		voi = vtk.vtkExtractVOI()
		voi.SetInput(image_in)
		voi.SetVOI( extent[0]+offset[0], extent[1]-offset[0], 
            		extent[2]+offset[1], extent[3]-offset[1], 
            		extent[4]+offset[2], extent[5]-offset[2] )

		mirror = vtk.vtkImageReslice()
		mirror.SetInput(voi.GetOutput())
		mirror.SetOutputExtent(extent[0], extent[1], 
                       	  	   extent[2], extent[3], 
                           	   extent[4], extent[5])
		mirror.MirrorOn()
		mirror.Update()
	
		image_out = mirror.GetOutput()
		return image_out

#===============================================
# Arguments
#===============================================

parser = argparse.ArgumentParser (
    description="""The foundation for a library of python scripts that mimic Scanco
IPL software.""")

# Arguments for IPL_BOUNDING_BOX_CUT
parser.add_argument ("--border", type=int, default=[0,0,0],
        	help="Set border (default: %(default)s)")

# Arguments for IPL_CL_RANK_EXTRACT
parser.add_argument ("--first_rank", type=int, default=1,
       	 help="Set extract filter first_rank (default: %(default)s)")
parser.add_argument ("--last_rank", type=int, default=1,
         help="Set extract filter last_rank (default: %(default)s)")
	
# Arguments for IPL_CL_SLICEWISE_EXTRACT
parser.add_argument ("--lo_vol_fract_in_perc", type=float, default=25,
        help="Set slicewise extract lower fraction (default: %(default)s)")
parser.add_argument ("--up_vol_fract_in_perc", type=float, default=100,
        help="Set slicewise extract upper fraction (default: %(default)s)")
        
# Arguments for IPL_DILATION
parser.add_argument ("--dilate_distance", type=int, default=5,
        help="Set dilation filter distance (default: %(default)s)")
parser.add_argument ("--continuous_at_boundary", nargs= 3, type=int ,default=[0,0,0],
        help="Set continous boundary (default: %(default)s)")

# Arguments for IPL_EROSION
parser.add_argument ("--erode_distance", type=int, default=5,
        help="Set erosion filter distance (default: %(default)s)")

# Arguments for IPL_GAUSS_LP
parser.add_argument ("--sigma", type=float, default=1.0,
        help="Set Gaussian filter sigma (default: %(default)s)")
parser.add_argument ("--support", type=int, default=2,
        help="Set Gaussian filter support (default: %(default)s)")
        
# Arguments for IPL_MASKAIMPEEL
parser.add_argument ("--peel_iter", type=int, default=0,
        help="Set upper threshold (default: %(default)s)") 

# Arguments for IPL_OPEN     
parser.add_argument ("--open_distance", type=int, default=5,
        help="Set dilation filter distance (default: %(default)s)")  

# Arguments for IPL_SET_VALUE
parser.add_argument ("--value_object", type=float, default=127,
        help="Set object value (default: %(default)s)")
parser.add_argument ("--value_background", type=float, default=0,
        help="Set background value (default: %(default)s)")

# Arguments for IPL_THRESHOLD
parser.add_argument ("--lower_in_perm_aut_al", type=float, default=100.0,
        help="Set lower threshold (default: %(default)s)")
parser.add_argument ("--upper_in_perm_aut_al", type=float, default=100000.0,
        help="Set upper threshold (default: %(default)s)")
parser.add_argument ("--value_in_range", type=int, default=127,
    	help="Set value in range (default: %(default)s)")

# Arguments for IPL_ADD_OFFSET_MIRROR
parser.add_argument ("--offset", nargs = 3, type=int, default=[0,0,0],
        help="Set offset (default: %(default)s)")
        
# Arguments for input and output filenames
parser.add_argument ("input")

args = parser.parse_args()

input = args.input
border = args.border
first_rank = args.first_rank
last_rank = args.last_rank
lower_fract = args.lo_vol_fract_in_perc
upper_fract = args.up_vol_fract_in_perc
value_in = args.value_in_range
boundary = args.continuous_at_boundary
dilate_distance = args.dilate_distance
erode_distance = args.erode_distance
lower = args.lower_in_perm_aut_al
upper = args.upper_in_perm_aut_al
value_in_range = args.value_in_range
peel_iter = args.peel_iter
open = args.open_distance
value_object = args.value_object
value_background = args.value_background
sigma = args.sigma
support = args.support

reader = vtkn88.vtkn88AIMReader()
reader.SetFileName(input)
reader.GlobalWarningDisplayOff()
reader.Update()