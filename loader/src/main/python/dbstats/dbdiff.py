'''
diff report between two genemania database releases
'''

import sys, os
import sqlite3

import buildstatsdb, utils
import attrdiff, nwdiff, iddiff, ontdiff, orgdiff

# for quick testing, assign a particular organism id, otherwise
# leave as None
TEST_ORG_ID = None

def getStatsDbName(dbDir, orgid):
    return os.path.join(dbDir, "%s" % orgid, "summary.sqlite")

def diffOrg(conn, org_name, dbDir1, orgid1, dbDir2, orgid2, reportDir, db1Name, db2Name):
    '''
    execute the comparisons and generate report html for two organisms,
    one from each of the two db's being compared
    '''

    # attach the first db as 'old', the second as 'new'
    olddb = newdb = None
    if orgid1:
        statsdbname1 = getStatsDbName(dbDir1, orgid1)
        conn.execute("attach '%s' as old" % statsdbname1)
        olddb = 'old'
    
    if orgid2:
        statsdbname2 = getStatsDbName(dbDir2, orgid2)        
        conn.execute("attach '%s' as new" % statsdbname2)
        newdb = 'new'
        
    # each organisms report data does into a separate folder
    # by organism name
    orgReportDir = os.path.join(reportDir, org_name)
    try:
        os.makedirs(orgReportDir)
    except:
        pass
                
    # basic organism summary numbers
    r = orgdiff.OrgDiff(conn, org_name)
    org_diff_data = r.diff(olddb, newdb)
                
    # annotations report
    r = ontdiff.OntologyDiff(conn, org_name)
    data = r.diff(olddb, newdb)
    data['dataset_old'] = db1Name
    data['dataset_new'] = db2Name

    utils.create_report(data, "annotations.html", os.path.join(orgReportDir, "annotations.html"))

    # identifiers report
    r = iddiff.IdentifierDiff(conn, org_name)
    data = r.diff(olddb, newdb)
    data['dataset_old'] = db1Name
    data['dataset_new'] = db2Name
    
    utils.create_report(data, "identifiers.html", os.path.join(orgReportDir, "identifiers.html"))

    if olddb and newdb:
        r.write_split_data(os.path.join(orgReportDir, "identifier_splits.tsv"))
        r.write_join_data(os.path.join(orgReportDir, "identifier_joins.tsv"))
        r.write_gained_identifiers(os.path.join(orgReportDir, "identifiers_gained.tsv"))
        r.write_lost_identifiers(os.path.join(orgReportDir, "identifiers_lost.tsv"))
    
    # networks report
    r = nwdiff.NetworkDiff(conn, org_name)

    data = r.diff(olddb, newdb)
    data['dataset_old'] = db1Name
    data['dataset_new'] = db2Name

    utils.create_report(data, "networks.html", os.path.join(orgReportDir, "networks.html"))
    r.write_network_data(os.path.join(orgReportDir, "networks.csv"))
    
    # attributes report
    r = attrdiff.AttributesDiff(conn, org_name)
    
    data = r.diff(olddb, newdb)
    data['dataset_old'] = db1Name
    data['dataset_new'] = db2Name
    
    utils.create_report(data, "attributes.html",  os.path.join(orgReportDir, "attributes.html"))    
        
    # detach db's
    if orgid1:
        conn.execute("detach old")
    
    if orgid2:
        conn.execute("detach new")

    return org_diff_data
    
def main(dbDir1, dbDir2, reportDir):    

    try:
        os.mkdir(reportDir)
    except:
        pass
   
    # use the folder names to identify db's in the reports
    db1Name = os.path.basename(dbDir1)
    db2Name = os.path.basename(dbDir2)
        
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    r = buildstatsdb.OrganismReport(conn, dbDir1, dbDir2)
    r.loadall()
    lost_organisms, common_organisms, gained_organisms  = r.getMatchedOrganisms()
    conn.close()
        
    org_totals = [] # list of dicts for each organism
    for common_org in common_organisms:
        orgid1, orgid2, org_name = common_org['old_id'], common_org['new_id'], common_org['Name']

        if TEST_ORG_ID and orgid1 != TEST_ORG_ID:
            continue
            
        print("comparing "+ dbDir1 + "/" + str(orgid1) + " with " + dbDir2 + "/" + str(orgid2))
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        
        try:
            
            org_diff_data = diffOrg(conn, org_name, dbDir1, orgid1, dbDir2, orgid2, reportDir, db1Name, db2Name)
            org_totals.append(org_diff_data)

        finally:
            conn.close()

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    
    try:    
        # gained/lost summaries
        lost_totals = []
        for lost_organism in lost_organisms:
            orgid = lost_organism[0]
            org_name = lost_organism[1]
            print("computing totals from lost organism "+ org_name +  " in " + dbDir1 + "/" + str(orgid))
            
            org_diff_data = diffOrg(conn, org_name, dbDir1, orgid, None, None, reportDir, db1Name, db2Name)
            lost_totals.append(org_diff_data)

        gained_totals = []
        for gained_organism in gained_organisms:
            # tuple assignment not working ... why? sqlite.ROW 2.5 bug?
            orgid = gained_organism[0]
            org_name = gained_organism[1]
            print("computing totals from gained organism " + orgn_name + " in " + dbDir2 + "/" + str(orgid))
            
            org_diff_data = diffOrg(conn, org_name, None, None, dbDir2, orgid, reportDir, db1Name, db2Name)
            gained_totals.append(org_diff_data)
    
    finally:
        conn.close()
    
    # top-level report page
    data = {}
    data['dataset_old'] = db1Name
    data['dataset_new'] = db2Name
    data['maintained'] = org_totals
    data['lost'] = lost_totals
    data['gained'] = gained_totals    
    utils.create_report(data, "index.html", os.path.join(reportDir, "index.html"))

    print("done")
    
if __name__ == '__main__':
    
    dbDir1 = sys.argv[1]
    dbDir2 = sys.argv[2]
    reportDir = sys.argv[3]

    main(dbDir1, dbDir2, reportDir)
