import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import sys
import os

#Read in thickness mpas for each subject (already grouped into each knee/bone)
infile = sys.argv[1]
basename = os.path.basename(infile)
name = basename.split("_L")[0]
dirname_read = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/PNG_Original/"
dirname_write = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/PNG_Original/Compiled_per_Subject/"
end1 = "_L_F.png"
end2 = "_L_T.png"
end3 = "_R_F.png"
end4 = "_R_T.png"
filename1 = dirname_read + name + end1
filename2 = dirname_read + name + end2
filename3 = dirname_read + name + end3
filename4 = dirname_read + name + end4
filename5 = dirname_write + name + ".png"

image1 = mpimg.imread(filename1)
image2 = mpimg.imread(filename2)
image3 = mpimg.imread(filename3)
image4 = mpimg.imread(filename4)

#Add plots together
plot = plt.figure()
plot.add_subplot(2,2,2)
plt.imshow(image1)
plt.gca().axes.get_xaxis().set_visible(False)
plt.gca().axes.get_yaxis().set_visible(False)
plt.axis('off')
plt.subplots_adjust(wspace=0, hspace=0)

plot.add_subplot(2,2,4)
plt.imshow(image2)
plt.gca().axes.get_xaxis().set_visible(False)
plt.gca().axes.get_yaxis().set_visible(False)
plt.axis('off')
plt.subplots_adjust(wspace=0, hspace=0)

plot.add_subplot(2,2,1)
plt.imshow(image3)
plt.gca().axes.get_xaxis().set_visible(False)
plt.gca().axes.get_yaxis().set_visible(False)
plt.axis('off')
plt.subplots_adjust(wspace=0, hspace=0)

plot.add_subplot(2,2,3)
plt.imshow(image4)
plt.gca().axes.get_xaxis().set_visible(False)
plt.gca().axes.get_yaxis().set_visible(False)
plt.axis('off')
plt.subplots_adjust(wspace=0, hspace=0)
plt.suptitle(name)
plt.tight_layout()
plot.savefig(filename5, transparent=True, bbox_inches='tight')
