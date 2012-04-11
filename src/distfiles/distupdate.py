import sys, os, md5

def getFileList(directory='..'):
    ret = ''
    for filename in os.listdir(directory):
        # Do md5 check to make sure the file downloaded properly
        if not ((filename.find(os.path.split(sys.argv[0])[1]) > -1) or
                (filename.find("version.dat") > -1) or
                (filename.find(".pyc") > -1)):               
            checksum = md5.new()
            try:
                f = file(directory+"/"+filename, 'rb')
                
                # Although the files are small, we can't guarantee the available memory nor that there
                # won't be large files in the future, so read the file in small parts (1kb at time)
                while True:
                        part = f.read(1024)
                        
                        if not part: 
                                break # end of file
                
                        checksum.update(part)
                        
                f.close()
                ret += '{"name":"%s","md5":"%s"}' % (filename, checksum.hexdigest()) + ","
            except:
                pass

    return ret[:-1]
    
if __name__ == '__main__':
    filelist = getFileList('..')
    app_path = os.path.realpath('..')
    sys.path.append(app_path)
    import settings
    APP_VERSION = settings.APP_VERSION
    del settings

    output = ''.join('{"version":"%s","files":[' % APP_VERSION)
    output += getFileList() + ']}'
    f = file('../version.dat', 'w')
    f.write(output)
    f.close()
    print output

