import glob
import os
import shutil
import stat

import numpy as np
import os

class Dgram:
    def __init__(self,f):
        self._nwords = 10
        self._data = np.fromfile(f,dtype=np.uint32,count=self._nwords)
        self.f = f
    def write(self):
        self._data.tofile(self.f)
    def clocklow(self): return self._data[0]
    def clockhigh(self): return self._data[1]
    def tslow(self): return self._data[2]
    def tshigh(self): return self._data[3]
    def env(self): return self._data[4]
    def setenv(self,value): self._data[4]=value
    def dmg(self): return self._data[5]
    def srclog(self): return self._data[6]
    def srcphy(self): return self._data[7]
    def contains(self): return self._data[8]
    def extent(self): return self._data[9]
    def next(self): return self.extent()+5*4 # 5*4 is size of Xtc
    def data(self): return self._data

def fixRunNumber(fname):
    fstat = os.stat(fname).st_mode
    os.chmod(fname, fstat | stat.S_IWUSR)
    # to fix the run number in the "env" field of the beginrun datagram
    newrun = int(os.path.basename(fname).split('-')[1][1:])
    f = open(fname,'r+')
    configdg = Dgram(f)
    f.seek(configdg.next())
    beginrunoffset = f.tell()
    beginrundg = Dgram(f)
    f.seek(beginrunoffset)
    beginrundg.setenv(newrun)
    beginrundg.write()

    #check
    f.seek(beginrunoffset)
    newbeginrundg = Dgram(f)
    #print beginrundg.data()
    #print newbeginrundg.data()
    assert newbeginrundg.env()==newrun, 'Read incorrect run number %d %d'%(newrun,newbeginrundg.env())
    f.close()
    os.chmod(fname, fstat)

def safecopy(inf,outf):
    if not os.path.isfile(inf):
        print '*** Input file',inf,'does not exist. Not copied'
        return
    if os.path.isfile(outf):
        print '*** Output file',outf,'exists. Not copied'
        return
    print 'cp',inf,outf
    shutil.copyfile(inf,outf)
    return

# assumes just one set of constants for now, using the first run
def copyconstants(hutch,expt,inruns,outruns):
    from PSCalib.CalibFileFinder import CalibFileFinder
    cdir = os.path.join('/reg/d/psdm',hutch,expt,'calib')
    groupdirs = glob.glob(os.path.join(cdir,'*'))
    for groupdir in groupdirs:
        group = os.path.basename(groupdir)
        sourcedirs = glob.glob(os.path.join(groupdir,'*'))
        for sourcedir in sourcedirs:
            src = os.path.basename(sourcedir)
            typedirs = glob.glob(os.path.join(sourcedir,'*'))
            for typedir in typedirs:
                type = os.path.basename(typedir)
                cff = CalibFileFinder(cdir, group, pbits=0)
                inf = cff.findCalibFile(src, type, inruns[0])
                if inf is '':
                    print '*** No',type,'calibration constants found for exp=%s:run=%d. Constants not copied'%(expt,inruns[0])
                    continue
                outcdir = os.path.join(outtopdir,'calib',group,src,type)
                if not os.path.isdir(outcdir):
                    print '*** Creating directory',outcdir
                    os.makedirs(outcdir)
                outf = os.path.join(outcdir,'%d-%d.data'%(outruns[0],outruns[-1]))
                safecopy(inf,outf)

class exptruns:
    def __init__(self,expt,inruns,outruns_start):
        self.expt = expt
        self.inruns = inruns
        self.outruns_start = outruns_start

exptlist = []
#exptlist.append(exptruns('xppc0114',[287],160))
#exptlist.append(exptruns('xppc0115',[270],170))
#exptlist.append(exptruns('xppf2115',[189,190,192],180))
#exptlist.append(exptruns('xpp72213',[324,300],190))
#exptlist.append(exptruns('xppd0115',[375,366],200))
#exptlist.append(exptruns('xppi3815',[224,225],210))
#exptlist.append(exptruns('xppi3815',range(100,105),220))
#exptlist.append(exptruns('xpph4915',[17],230))
#exptlist.append(exptruns('xppc0115',[328,335],240))
#exptlist.append(exptruns('xpp02016',[225,272,300],250))
#exptlist.append(exptruns('xcs01116',[81,82,83,120],260))
#exptlist.append(exptruns('cxi06216',[22],270))
#exptlist.append(exptruns('amoi0216',[32,34],280))
#exptlist.append(exptruns('amoc0113',[217,219],290))
#exptlist.append(exptruns('diamcc14',[920,921,922],300))
#exptlist.append(exptruns('amol9416',[272],310))
#exptlist.append(exptruns('xppl4416',[283,284],320))
#exptlist.append(exptruns('sxr82112',[197],330))
#exptlist.append(exptruns('cxi12016',[24],30))
exptlist.append(exptruns('amo06516',[10,15,19],340))

rootdir = '/reg/d/psdm'
datadirs = ['xtc/index','xtc/smalldata','xtc']
outtopdir = os.path.join(rootdir,'xpp/xpptut15')
for e in exptlist:
    expt = e.expt
    inruns = e.inruns
    outruns_start = e.outruns_start
    hutch = expt[:3]
    outruns = range(outruns_start,outruns_start+len(inruns)+1)
    copyconstants(hutch,expt,inruns,outruns)
    for dd in datadirs:
        outfiles = []
        outdir = os.path.join(outtopdir,dd)
        for rin,rout in zip(inruns,outruns):
            infs = glob.glob(os.path.join(rootdir,hutch,expt,dd,'*r%4.4d*'%rin))
            if len(infs)==0:
                print '*** No input files found for exp=%s:run=%d'%(expt,rin),'in directory',dd
            for inf in infs:
                _,outf = os.path.split(inf)
                outf = os.path.join(outdir,'e665-r'+ ('%4.4d'%rout) + outf[10:])
                safecopy(inf,outf)
                if outf.endswith('.xtc'): fixRunNumber(outf)
