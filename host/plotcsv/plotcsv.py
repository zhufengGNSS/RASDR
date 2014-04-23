#import math
#import time
import sys
import datetime
import numpy as np
from matplotlib import pyplot as plt

DEF_DELIM   = ','
DEF_AVERAGE = 1

def excel2dt(et):
    # http://stackoverflow.com/questions/1703505/excel-date-to-unix-timestamp
    # http://stackoverflow.com/questions/3682748/converting-unix-timestamp-string-to-readable-date-in-python
    ts = (et - 25569)*86400 # 25569 is days since 1900-01-01
    ts = ts + (4*60*60)     # timezone EST5EDT
    return datetime.datetime.fromtimestamp(float(ts))

def dt2excel(dt):
    # http://stackoverflow.com/questions/9574793/how-to-convert-a-python-datetime-datetime-to-excel-serial-date-number
    delta = dt - datetime.datetime(1899, 12, 29)    # set w/r/t excel2dt() date; NB: do not know why this must be set 3 days earlier
    return float(delta.days) + (float(delta.seconds) / 86400)

def generate_spectrum_plots(filename,opts):
    if opts.paul:
        # this is Paul's "Excel-optimized" .csv format
        # http://stackoverflow.com/questions/13311471/skip-a-specified-number-of-columns-with-numpy-genfromtxt
        # http://stackoverflow.com/questions/466345/converting-string-into-datetime
        #
        # yes, I know it is very silly to go into a datetime, then down into an excel datetime
        # only to go back to a datetime to plot everything.

        from StringIO import StringIO

        f=open(filename,'r')
        d=np.genfromtxt(StringIO(f.readline()),delimiter=opts.delimiter,dtype='str')[4]    # Paul puts the creation date in row1,col4
        d=d.replace('"','')     # remove the extra ""
        t=np.genfromtxt(f,delimiter=opts.delimiter,usecols=[0],dtype='str')
        f.seek(0)
        f.readline()
        data = np.genfromtxt(f,delimiter=opts.delimiter,dtype='float')
        lastcol = data.shape[1]-1
        for i in range(1,t.shape[0]):
            data[i,0] = dt2excel(datetime.datetime.strptime(d+'T'+t[i], '%m/%d/%yT%H:%M:%S'))
        data = data[:,:lastcol] # cut out the last column from Paul's data, its junk
    else:
        # this is the proposed .csv format
        data = np.genfromtxt(filename,delimiter=opts.delimiter)
    s_a  = data[1:,1:]
    ts_a = data[1:,0]
    fMHz = data[0,1:]
    zidx = np.searchsorted(fMHz,0)
    nbin = len(fMHz)
    lastrow = s_a.shape[0]-1

    if opts.verbose:
        print 'spectra=',s_a.shape[0]
        print 'range (MHz)','=[',fMHz.min(),',',fMHz.max(),']'
        print 'zero index=',zidx
        print 'frequency bins=',nbin
        if s_a.shape[0] > 2:
            delta = excel2dt(ts_a[lastrow]) - excel2dt(ts_a[lastrow-1])
            print 'start=',excel2dt(ts_a[0])
            print 'end  =',excel2dt(ts_a[lastrow])
            print 'seconds between samples=',delta.seconds
        print 'averaging=',opts.average

    acc = np.zeros(nbin)
    n   = 0
    for fr in range(np.shape(s_a)[0]):
        dt = excel2dt(ts_a[fr])
        s = s_a[fr]
        if opts.canceldc:
            if opts.verbose:
                print 'Cancel DC: frq',fMHz[zidx-4:zidx+5]
                print 'Cancel DC: b4 ',s[zidx-4:zidx+5]
            a = (s[zidx-1] + s[zidx+1])/2.0
            if a < s[zidx]:
                s[zidx] = a
            if opts.verbose:
                print 'Cancel DC: ftr',s[zidx-4:zidx+5]
        if n == 0:
            tstart = dt.strftime('%Y-%m-%dT%H:%M:%S')
        n    = n+1
        acc += s_a[fr]
        if n >= opts.average or fr == lastrow:
            s   = acc / float(n)
            min = np.floor(s.min())-1.0
            max = np.ceil(s.max())+1.0
            tstop = dt.strftime('%Y-%m-%dT%H:%M:%S')
            if n > 1:
                title = 'Collected between %s and %s\nAveraged over %d frames'%(tstart,tstop,n)
            else:
                title = 'Collected at %s'%tstop

            plt.plot(fMHz,s,hold=False)
            plt.axis([fMHz[0],fMHz[nbin-1],min,max])
            plt.xlabel('frequency (MHz)')
            plt.ylabel('spectral power (arbitrary unit)')
            plt.title(title)

            name = 'spectrum-%s.png'%dt.strftime('%Y_%b_%d_%H_%M_%S')
            plt.savefig(name)
            print 'Saved '+name

            acc = np.zeros(nbin)
            n   = 0

if __name__ == '__main__':
    from optparse import OptionParser

    p = OptionParser()
    p.set_usage('plotcsv.py <filename.csv> [options]')
    p.set_description(__doc__)
    p.add_option('-a', '--average', dest='average', type='int', default=DEF_AVERAGE,
        help='Specify the number of spectra to average for each plot; default=%d'%DEF_AVERAGE)
    p.add_option('-c', '--cancel-dc', dest='canceldc', action='store_true', default=False,
        help='Cancel out component at frequency bin for 0Hz')
    p.add_option('-d', '--delimiter', dest='delimiter', type='str', default=DEF_DELIM,
        help='Specify the delimiter character to use; default=%s'%DEF_DELIM)
    p.add_option('-p', '--paul', dest='paul', action='store_true', default=False,
        help='Indicate that .csv file is in Paul\'s format')
    p.add_option('-v', '--verbose', dest='verbose', action='store_true', default=False,
        help='Verbose')
    opts, args = p.parse_args(sys.argv[1:])

    if args==[]:
        print 'Please specify a filename. Run with the -h flag to see all options.\n'
    else:
        generate_spectrum_plots(args[0],opts)
