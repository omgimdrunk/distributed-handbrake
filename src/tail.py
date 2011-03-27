def tail( f, window=20 ):
    f.seek( 0, 2 )
    bytes= f.tell()
    size= window
    block= -1
    while size > 0 and bytes+block*1024  > 0:
        f.seek( block*1024, 2 )
        data= f.read( 1024 )
        linesFound= data.count('\n')
        size -= linesFound
        block -= 1
    block += 1
    f.seek( block*1024, 2 )
    f.readline()
    lastBlocks= list( f.readlines() )
    print lastBlocks[-window:]