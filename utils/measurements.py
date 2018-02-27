import numpy as np
from sklearn.utils.linear_assignment_ import linear_assignment
from bbox import bbox_overlap
VERBOSE = False
def clear_mot_hungarian(stDB, gtDB, threshold):
    st_frames = np.unique(stDB[:, 0])
    gt_frames = np.unique(gtDB[:, 0])
    st_ids = np.unique(stDB[:, 1])
    gt_ids = np.unique(gtDB[:, 1])
    f_gt = int(max(max(st_frames), max(gt_frames)))  
    n_gt = int(max(gt_ids)) 
    n_st = int(max(st_ids)) 
    #f_gt = len(gt_frames)
    #n_gt = len(gt_ids)
    #n_st = len(st_ids)

    mme = np.zeros((f_gt, ), dtype=float)          # ID switch in each frame
    c = np.zeros((f_gt, ), dtype=float)            # matches found in each frame
    fp = np.zeros((f_gt, ), dtype=float)           # false positives in each frame
    missed = np.zeros((f_gt, ), dtype=float)       # missed gts in each frame
    
    g = np.zeros((f_gt, ), dtype=float)            # gt count in each frame
    d = np.zeros((f_gt, n_gt), dtype=float)         # overlap matrix
    allfps = np.zeros((f_gt, n_st), dtype=float)
    
    gt_inds = [{} for i in xrange(f_gt)]
    st_inds = [{} for i in xrange(f_gt)]
    M = [{} for i in xrange(f_gt)]                  # matched pairs hashing gid to sid in each frame 

    # hash the indices to speed up indexing
    for i in xrange(gtDB.shape[0]):
        frame = int(gtDB[i, 0]) - 1
        gid = int(gtDB[i, 1])
        gt_inds[frame][gid - 1] = i

    for i in xrange(stDB.shape[0]):
        frame = int(stDB[i, 0]) - 1
        sid = int(stDB[i, 1])
        st_inds[frame][sid] = i

    for t in xrange(f_gt):
        g[t] = len(gt_inds[t].keys()) 
        
        if t > 0:
            mappings = M[t - 1].keys()
            sorted(mappings)
            for k in xrange(len(mappings)):
                if mappings[k] in gt_inds[t].keys() and M[t - 1][mappings[k]] in st_inds[t].keys():
                    row_gt = gt_inds[t][mappings[k]]
                    row_st = st_inds[t][M[t - 1][mappings[k]]]
                    dist = bbox_overlap(stDB[row_st, 2:6], gtDB[row_gt, 2:6])
                    if dist >= threshold:
                        M[t][mappings[k]] = M[t - 1][mappings[k]]
                        if VERBOSE:
                            print 'perserving mapping: %d to %d'%(mappings[k], M[t][mappings[k]])
        unmapped_gt, unmapped_st  = [], []
        unmapped_gt = [key for key in gt_inds[t].keys() if key not in M[t].keys()]
        unmapped_st = [key for key in st_inds[t].keys() if key not in M[t].values()]
        if len(unmapped_gt) > 0 and len(unmapped_st) > 0: 
            overlaps = np.zeros((n_gt, n_st), dtype=float)
            for i in xrange(len(unmapped_gt)):
                row_gt = gt_inds[t][unmapped_gt[i]]
                for j in xrange(len(unmapped_st)):
                    row_st = st_inds[t][unmapped_st[j]]
                    dist = bbox_overlap(stDB[row_st, 2:6], gtDB[row_gt, 2:6])
                    if dist >= threshold:
                        overlaps[i][j] = dist
            matched_indices = linear_assignment(1 - overlaps)
            
            for matched in matched_indices:
                if overlaps[matched[0], matched[1]] == 0:
                    continue
                M[t][unmapped_gt[matched[0]]] = unmapped_st[matched[1]]
                if VERBOSE:
                    print 'adding mapping: %d to %d'%(unmapped_gt[matched[0]], M[t][unmapped_gt[matched[0]]])
        cur_tracked = M[t].keys()
        st_tracked = M[t].values()
        fps = [key for key in st_inds[t].keys() if key not in M[t].values()] 
        for k in xrange(len(fps)):
            allfps[t][fps[k]] = fps[k]

        # check miss match errors
        if t > 0:
            for i in xrange(len(cur_tracked)):
                ct = cur_tracked[i]
                est = M[t][ct]
                last_non_empty = -1
                for j in range(t - 1, 0, -1):
                    if ct in M[j].keys():
                        last_non_empty = j
                        break
                if ct in gt_inds[t - 1].keys() and last_non_empty != -1:
                    mtct, mlastnonemptyct = -1, -1
                    if ct in M[t]:
                        mtct = M[t][ct]
                    if ct in M[last_non_empty]:
                        mlastnonemptyct = M[last_non_empty][ct]

                    if mtct != mlastnonemptyct:
                        mme[t] += 1
        c[t] = len(cur_tracked)
        fp[t] = len(st_inds[t].keys())
        fp[t] -= c[t]
        missed[t] = g[t] - c[t]
        for i in xrange(len(cur_tracked)):
            ct = cur_tracked[i]
            est = M[t][ct]
            row_gt = gt_inds[t][ct]
            row_st = st_inds[t][est]
            d[t][ct] = bbox_overlap(stDB[row_st, 2:6], gtDB[row_gt, 2:6])
        
    return mme, c, fp, g, missed, d, M, allfps

def idmeasures(gtDB, stDB, threshold):
    st_ids = np.unique(stDB[:, 1])
    gt_ids = np.unique(gtDB[:, 1])
    n_st = len(st_ids)
    n_gt = len(gt_ids)
    groundtruth = [gtDB[np.where(gtDB[:, 1] == i)[0], :] for i in xrange(n_gt)]
    prediction = [stDB[np.where(stDB[:, 1] == i)[0], :] for i in xrange(n_st)]
    cost = np.zeros((n_gt + n_st, n_st + n_gt), dtype=float)
    cost[n_gt:, :n_st] = float('inf')
    cost[:n_gt, n_st:] = float('inf')
    
    fp = np.zeros(cost.shape)
    fn = np.zeros(cost.shape)

    cost_block, fp_block, fn_block = cost_between_gt_pred(groundtruth, prediction, threshold)

    cost[:n_gt, :n_st] = cost_block
    fp[:n_gt, :n_st] = fp_block
    fn[:n_gt, :n_st] = fn_block

    # computed trajectory match no groundtruth trajectory, FP
    for i in xrange(n_st):
        cost[i + n_gt:, i] = prediction[i].shape[0]
        fp[i + n_gt:, i] = prediction[i].shape[0]
    
    # groundtruth trajectory match no computed trajectory, FN
    for i in xrange(n_gt):
        cost[i, i + n_st] = groundtruth[i].shape[0]
        fn[i, i + n_st] = groundtruth[i].shape[0]
    
    
    matched_indices = linear_assignment(cost)

    nbox_gt = sum([groundtruth[i].shape[0] for i in xrange(n_gt)])
    nbox_st = sum([prediction[i].shape[0] for i in xrange(n_st)])
    
    IDFP = 0
    IDFN = 0
    for matched in matched_indices:
        IDFP += fp[matched[0], matched[1]]
        IDFN += fn[matched[0], matched[1]]

    IDTP = nbox_gt - IDFN

    assert IDTP == nbox_gt - IDFP
    IDP = IDTP / (IDTP + IDFP) * 100               # IDP = IDTP / (IDTP + IDFP)
    IDR = IDTP / (IDTP + IDFN) * 100               # IDR = IDTP / (IDTP + IDFN)
    IDF1 = 2 * IDTP / (nbox_gt + nbox_st) * 100    # IDF1 = 2 * IDTP / (2 * IDTP + IDFP + IDFN)

    measures = edict()
    measures.IDP = IDP
    measures.IDR = IDR
    measures.IDF1 = IDF1
    measures.IDTP = IDTP
    measures.IDFP = IDFP
    measures.IDFN = IDFN
    measures.nbox_gt = nbox_gt
    measures.nbox_st = nbox_st

    return measures

def corresponding_frame(traj1, len1, traj2, len2):
    p1, p2 = 0, 0
    loc = np.zeros((len1, ), dtype=int)
    while p1 < len1 and p2 < len2:
        if traj1[p1] < traj2[p2]:
            loc[p1] = -1
            p1 += 1
        elif traj1[p1] == traj2[p2]:
            loc[p1] = p2
            p1 += 1
            p2 += 1
        else:
            p2 += 1
    return loc

def compute_distance(traj1, traj2, matched_pos):
    distance = np.zeros((len(matched_pos), ), dtype=float)
    for i in xrange(len(matched_pos)):
        if matched_pos[i] == -1:
            continue
        else:
            iou = bbox_overlap(traj1[i, 2:6], traj2[matched_pos[i], 2:6])
            distance[i] = iou
    return distance

def cost_between_trajectories(traj1, traj2, threshold):
    [npoints1, dim1] = traj1.shape
    [npoints2, dim2] = traj2.shape
    
    # find start and end frame of each trajectories
    start1 = traj1[0, 0]
    end1 = traj1[-1, 0]
    start2 = traj2[0, 0]
    end2 = traj2[-1, 0]

    ## check frame overlap
    has_overlap = max(start1, start2) <= min(end1, end2)
    if not has_overlap:
        return npoints1, npoints2
    
    matched_pos1 = corresponding_frame(traj1[:, 0], npoints1, traj2[:, 0], npoints2)
    matched_pos2 = corresponding_frame(traj2[:, 0], npoints2, traj1[:, 0], npoints1)
    dist1 = compute_distance(traj1, traj2, matched_pos1)
    dist2 = compute_distance(traj2, traj1, matched_pos2)

    err1 = sum([1 for i in xrange(npoints1) if dist1[i] < threshold]) 
    err2 = sum([1 for i in xrange(npoints2) if dist2[i] < threshold]) 
    return err1, err2

def cost_between_gt_pred(groundtruth, prediction, threshold):
    n_gt =  len(groundtruth)
    n_st = len(prediction)
    cost = np.zeros((n_gt, n_st), dtype=float)
    fp = np.zeros((n_gt, n_st), dtype=float)
    fn = np.zeros((n_gt, n_st), dtype=float)
    for i in xrange(n_gt):
        for j in xrange(n_st):
            fp[i, j], fn[i, j] = cost_between_trajectories(groundtruth[i], prediction[j], threshold)
            cost[i, j] = fp[i, j] + fn[i, j]
    return cost, fp, fn
