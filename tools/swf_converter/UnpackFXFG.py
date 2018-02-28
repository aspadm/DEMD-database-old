import os.path
import struct
import sys

def unpack_swf(orig_path, out_folder, filename):
    """Create .swf file and DDS textures from packed file

    Args:
        orig_path: source file (magic is FXGF)
        out_folder: where to place files; ended with /
        filename: how to name .swf file
    """

    if not os.path.isfile(orig_path):
        print("Source file not exist!")
        sys.exit(1)

    if not os.path.isdir(out_folder):
        print("Create out folder")
        os.mkdir(out_folder)

    if out_folder[-1] != "/" or out_folder[-1] != "\\":
        out_folder += "/"

    if filename[-4:] != ".swf":
        filename += ".swf"
    
    with open(orig_path, "rb") as file:
        filesize = os.path.getsize(orig_path)

        if file.read(4) != b'FXFG':
            print("Not a .swf file!")
            sys.exit(3)

        last_pos = 4; # position in file

        while last_pos < filesize:
            if file.read(3) == b'GFX':
                last_pos += 3
                print('Found "GFX" subfile at', last_pos - 3)
                break
            else:
                last_pos += 1
                file.seek(-2, os.SEEK_CUR)

        with open(out_folder + filename, "wb") as new_swf:
            new_swf.write(b'FWS')
            names = [] # DDS filenames
            action = 0 # 0 - search, 1 - store name, 2 - store DDS
            subpos = 0 # position in subfile
            subsize = 0 # subfile size
            last_dds = 0
            
            while last_pos < filesize:
                last_pos += 1
                last = file.read(1)
                subpos += 1

                if action == 0:
                    if last == b'D':
                        last = file.read(3)

                        if last == b'DS\x20':
                            print('Found "DDS" subfile at', last_pos - 1)
                            action = 2
                            dds_file = open(out_folder + names[last_dds], "wb")
                            last_dds += 1
                            subpos = 0
                            file.seek(last_pos - 5)
                            subsize = struct.unpack('L', file.read(4))[0]

                        last = b'D'
                        file.seek(last_pos)
                    elif last == b'a':
                        last = file.read(8)

                        if last == b'ssembly:':
                            print('Found subfile name  at', last_pos - 1)
                            action = 1
                            names.append(b'')
                            subpos = 0

                        last = b'a'
                        file.seek(last_pos)
                        
                if action == 1:
                    if last == b'\x00':
                        action = 0
                        names[-1] = names[-1].decode("ASCII")
                        names[-1] = names[-1][names[-1].rfind('/') + 1:]
                    elif subpos > 10:
                        names[-1] += last
                elif action == 2:
                    if subpos < subsize:
                        dds_file.write(last)
                    else:
                        action = 0
                        dds_file.close()
                    
                new_swf.write(last)

            print()
            print("Exported", len(names), "DDS files")

if len(sys.argv) != 4:
    print("DEMD FXFG file unpacker (.swf)\nCreated by aspadm\n")
    print("Usage:\n\tUnpackFXFG source_file out_folder out_name")
else:
    unpack_swf(sys.argv[1], sys.argv[2], sys.argv[3])
