def next_generation(grid):

    temp_grid=[[0]+i+[0] for i in [[0]*len(grid[0])]+grid+[[0]*len(grid[0])]]

    update_live=[]
    update_death=[]
    for row in range(1,len(temp_grid)-1):
        for col in range(1,len(temp_grid[0])-1):

            ncount=sum (temp_grid[row+ dr][col + dc] for dr in (-1, 0, 1) for dc in (-1, 0, 1) if not (dr == 0 and dc == 0))

            if grid[row-1][col-1]==1:
                if ncount <2:
                    update_death.append((row-1,col-1))
                if ncount in [2,3]:
                    pass
                if ncount >3:
                    update_death.append((row-1,col-1))
            elif grid[row-1][col-1]==0:
                if ncount==3:
                    update_live.append((row-1,col-1))

    new_grid = [row[:] for row in grid]
    for cell in update_live:
        new_grid[cell[0]][cell[1]]=1

    for cell in update_death:
        new_grid[cell[0]][cell[1]]=0
            
    return new_grid