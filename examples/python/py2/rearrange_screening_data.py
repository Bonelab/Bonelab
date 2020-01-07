import sys
import os.path

if len(sys.argv) != 2:
  print "Usage: python chop infile.txt"
  sys.exit()

infilename = sys.argv[1]

print "Reading", infilename
infile = open(infilename)
lines = infile.readlines()

headerLength=4
chunkLength=6500
retainedLines=500
print "Header length is", headerLength
print "Chunk length is", chunkLength
print "Retained lines", retainedLines

header = lines[:headerLength]

# Get rid of everything except first 2 columns
#
twoCols = []
for line in lines[headerLength:]:
  tokens = line.split()
  twoCols.append(tokens[0] + '\t' + tokens[1])

columnHeaders = twoCols[:2]

# Split into chunks of 5000 lines
#
chunks = []
pos = 2   # Because we skip the column headings as well
while pos + retainedLines <= len(twoCols):
  chunks.append(columnHeaders + twoCols[pos:pos+retainedLines])
  pos += chunkLength
print "Found", len(chunks), " chunks"
print "Leftover lines:", len(twoCols)-pos, " (neg value means all were used)"

print "Retaining only last 6 chunks"
chunks = chunks[-6:]

# Function to concatenate corresponding lines of two lists of lines
#
def paste_lines(A, B):
  if len(A) != len(B):
    print "Oops, something went wrong"
    sys.exit()
  return [a + '\t' + b for (a, b) in zip(A, B)]

# Concatenate together all the even numbered chunks
positiveLines = ['']*len(chunks[0])
for chunk in chunks[::2]:
  positiveLines = paste_lines(positiveLines,chunk)
lineEndings = '\n'*len(chunks[0])
positiveLines = paste_lines(positiveLines,lineEndings)


# Concatenate together all the odd numbered chunks
negativeLines = ['']*len(chunks[0])
for chunk in chunks[1::2]:
  negativeLines = paste_lines(negativeLines,chunk)
negativeLines = paste_lines(negativeLines,lineEndings)

posFileName = os.path.splitext(infilename)[0] + "_pos.txt"
print "Writing even chunks to", posFileName
posFile = open(posFileName,"w")
posFile.writelines(header)
posFile.writelines(positiveLines)

negFileName = os.path.splitext(infilename)[0] + "_neg.txt"
print "Writing odd chunks to", negFileName
negFile = open(negFileName,"w")
negFile.writelines(negativeLines)
