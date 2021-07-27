'''
diff report between two genemania database releases
'''

import utils

class NetworkDiff(utils.Db):
    '''
    
    '''
    
    def __init__(self, conn, org_name):
        self.conn = conn
        self.org_name = org_name
    
    def createDiffTable(self):
        '''temporary reporting table'''
        
        
        # status is 'added', 'removed', or 'maintained'
        sql = '''
        drop table if exists network_diff;
        
        create temp table network_diff (Network_Group_Name text, Network_Name text, status text,
        old_source text, old_source_url text,
        new_source text, new_source_url text,
        old_id int, new_id int, 
        old_num_nodes int, new_num_nodes int,
        old_num_edges int, new_num_edges int,
        nodes_lost int, nodes_gained int);
        
        create index ix_network_diff on network_diff (Network_Group_Name, Network_Name);         
        '''
        
        self.executescript(sql)
    
    def diffNetworks(self, olddb = "old", newdb = "new"):
        '''
        results in new table, 'network_diff'
        '''
        
        self.createDiffTable()
        
        if not olddb and not newdb:
            raise Exception("can't compare nothing to noone!")
        
        networkGainSql = """
        INSERT INTO network_diff (network_group_name, network_name, status, 
        new_source, new_source_url, new_id, new_num_nodes, new_num_edges)
        SELECT t1.Network_Group_Name, t1.Network_Name, '%s',
        t1.source, t1.source_url, t1.network_id, t1.num_nodes, t1.num_edges 
        from %s.networks as t1;
        """

        networkLostSql = """
        INSERT INTO network_diff (network_group_name, network_name, status, 
        old_source, old_source_url, old_id, old_num_nodes, old_num_edges)
        SELECT t1.Network_Group_Name, t1.Network_Name, '%s',
        t1.source, t1.source_url, t1.network_id, t1.num_nodes, t1.num_edges 
        from %s.networks as t1;
        """
        
        if not olddb:            
            sql = networkGainSql % ('added', newdb)
            self.execute(sql)
                                
        elif not newdb:            
            sql = networkLostSql % ('removed', olddb)
            self.execute(sql)
        
        else:
       
            # note the sql here matches by both group and network name, since possibly the same
            # network name can be used in a different group. 
            networkGainSql = """
            INSERT INTO network_diff (network_group_name, network_name, status, 
            new_source, new_source_url, new_id, new_num_nodes, new_num_edges)
            SELECT t1.Network_Group_Name, t1.Network_Name, '%s',
            t1.source, t1.source_url, t1.network_id, t1.num_nodes, t1.num_edges 
            from %s.networks as t1 where not exists 
               (SELECT t2.Network_Group_Name, t2.Network_Name from %s.networks as t2 
                where t1.Network_Group_Name = t2.Network_Group_Name 
                and t1.Network_Name = t2.Network_Name);
            """

            networkLostSql = """
            INSERT INTO network_diff (network_group_name, network_name, status, 
            old_source, old_source_url, old_id, old_num_nodes, old_num_edges)
            SELECT t1.Network_Group_Name, t1.Network_Name, '%s',
            t1.source, t1.source_url, t1.network_id, t1.num_nodes, t1.num_edges 
            from %s.networks as t1 where not exists 
               (SELECT t2.Network_Group_Name, t2.Network_Name from %s.networks as t2 
                where t1.Network_Group_Name = t2.Network_Group_Name 
                and t1.Network_Name = t2.Network_Name);
            """
            
            sql = networkGainSql % ('added', newdb, olddb)
            self.execute(sql)
            
            sql = networkLostSql % ('removed', olddb, newdb)
            self.execute(sql)
                        
            # determine matches and build into list for analysis
            networkMatchSql = """
            INSERT INTO network_diff (Network_Group_Name, Network_Name, status, old_source, old_source_url, new_source, new_source_url, 
            old_id, new_id, old_num_nodes, new_num_nodes, old_num_edges, new_num_edges) 
            SELECT t1.Network_Group_Name, t1.Network_Name, 'maintained', t1.source, t1.source_url, t2.source, t2.source_url, 
               t1.Network_Id as old_id, t2.Network_Id as new_id,
               t1.Num_Nodes as old_num_nodes, t2.Num_Nodes as new_num_nodes,
               t1.Num_Edges as old_num_edges, t2.Num_Edges as new_num_edges
            from %s.networks as t1, %s.networks as t2 
            where t1.Network_Group_Name = t2.Network_Group_Name
            and t1.Network_Name = t2.Network_Name
            """
    
            sql = networkMatchSql % (olddb, newdb)
            self.execute(sql)
            networksMaintained = self.select("select * from network_diff;")
            print("maintained: " + str(networksMaintained)[1:-1])
    
    def diffNetworkDegrees(self, olddb = "old", newdb = "new"): 
        '''
        update a netdiff object by determining what nodes have been added 
        or have disappeared between versions of a network, by looking at
        the node degrees table
        '''
        
        sql = "select rowid, * from network_diff where status='maintained'"
        diffs = self.select(sql)
        
        for d in diffs:
            #print "netdiff for ", netDiff.group_name, netDiff.name
            #print "old num nodes, new num nodes: ", netDiff.old_num_nodes, netDiff.new_num_nodes
            print(str(d['Network_Name'].encode("utf8")))
            overlapSql = '''
            create temp table tmp as select t1.symbol as symbol from %s.degrees as t1 join %s.degrees as t2
            where t1.network_id = %s and t2.network_id = %s
            and t1.symbol = t2.symbol
            '''
            
            old_id = d['old_id']
            new_id = d['new_id']
            row_id = d['rowid']
            sql = overlapSql % (olddb, newdb, old_id, new_id)
            self.execute(sql)
            
            sql = "create index ix_tmp_sym on tmp (Symbol)"
            self.execute(sql)
            
            print("overlapping nodes" + str(self.selectNumber("select count(*) from tmp;")))
            
            lostSql = "select t1.Symbol from %s as t1 where t1.Network_ID = %s and t1.Symbol not in (select Symbol from tmp);"
            lost = self.select(lostSql % ('old.degrees', old_id))
            print("lost: " + str(len(lost)))
            
            gained = self.select(lostSql % ('new.degrees', new_id))
            print("gained: " + str(len(gained)))
            
            sql = "update network_diff set nodes_lost=%s, nodes_gained=%s where rowid=%s;" % (len(lost), len(gained), row_id)
            self.execute(sql)
            
            sql = self.executescript("drop table tmp;")
                
    def diffGroups(self, olddb = "old", newdb = "new"):
        '''
        determine network groups lost, maintained, and gained between two releases, 
        comparing by group name
        '''
                
        if not olddb and not newdb:
            raise Exception("can't compare nothing to noone!")
        
        groupsLost = groupsMaintained = groupsGained = []
        
        if not olddb:
            groupsSql = "SELECT distinct(Network_Group_Name) from %s.networks;"  
            sql = groupsSql % (newdb)
            results = self.select(sql)
            
            groupsGained = [result[0] for result in results]
            
            
        elif not newdb:
            groupsSql = "SELECT distinct(Network_Group_Name) from %s.networks;"  
            sql = groupsSql % (olddb)
            results = self.select(sql)
            
            groupsLost = [result[0] for result in results]
            
        else:
            
            # gained
            groupDiffSql = "SELECT distinct(Network_Group_Name) from %s.networks where Network_Group_Name not in (select distinct(Network_Group_Name) from %s.networks)" 
            sql = groupDiffSql % (newdb, olddb)
            results = self.select(sql)
            
            groupsGained = [result[0] for result in results]
            print(str(groupsGained)[1:-1])
            
            # lost
            sql = groupDiffSql % (olddb, newdb)
            results = self.select(sql)
            groupsLost = [result[0] for result in results]
            print(str(groupsLost)[1:-1])
            
            # maintained
            groupOverlapSql = "SELECT distinct(Network_Group_Name) from %s.networks where Network_Group_Name in (select distinct(Network_Group_Name) from %s.networks) order by Network_Group_Name"
            sql = groupOverlapSql % (olddb, newdb)
            results = self.select(sql)
            groupsMaintained = [result[0] for result in results]
            print(str(groupsMaintained)[1:-1])
        
        return groupsLost, groupsMaintained, groupsGained
        
    def createNetworkGroupReportData(self, group_name, olddb = "old", newdb = "new"):
        '''
        return a dictionary containing data to
        be interpolated into the report template
        
        the diff data should be generated in the network_diff table.        
        '''
        
        if not olddb and not newdb:
            raise Exception("can't compare nothing to noone!")
                
        d = {}
        d['Group'] = group_name

        d['maintained'] = self.select("select rowid, * from network_diff where status = 'maintained' and Network_Group_Name = '%s'" % group_name)
        d['gained'] = self.select("select rowid, * from network_diff where status = 'added' and Network_Group_Name = '%s'" % group_name)
        d['lost'] = self.select("select rowid, * from network_diff where status = 'removed' and Network_Group_Name = '%s'" % group_name)
        d['old_num_networks'] = 0        
        d['new_num_networks'] = 0
        d['sample_nodes_lost'] = []
        d['sample_nodes_added'] = []
                    
        if olddb:        
            d['old_num_networks'] = self.selectNumber("select count(*) from old.networks where Network_Group_Name = '%s'" % group_name)
            
        if newdb:
            d['new_num_networks'] = self.selectNumber("select count(*) from new.networks where Network_Group_Name = '%s'" % group_name)
         
        return d    
        
    def diff(self, olddb = "old", newdb = "new"):
        '''
        return a dictionary containing report data by querying
        stats db
        '''
                
        groups_lost, groups_maintained, groups_gained = self.diffGroups(olddb, newdb)
        self.diffNetworks(olddb, newdb)
        self.diffNetworkDegrees(olddb, newdb)
 
        data = {}
        data['name'] = self.org_name
 
        group_data = []
        for group_name in groups_maintained:
            network_report_data = self.createNetworkGroupReportData(group_name, olddb, newdb)
            network_report_data['width'] = 50*len(network_report_data['maintained'])
            group = {}
            group['name'] = group_name
            group['netchange'] = network_report_data['new_num_networks']- network_report_data['old_num_networks']
            group['status'] = 'maintained'
            group['details'] = network_report_data
            group_data.append(group)

        for group_name in groups_lost:
            network_report_data = self.createNetworkGroupReportData(group_name, olddb, newdb)
            group = {}
            group['name'] = group_name
            group['netchange'] = 0
            group['status'] = 'lost'
            group['details'] = network_report_data
            group_data.append(group)

        for group_name in groups_gained:
            network_report_data = self.createNetworkGroupReportData(group_name, olddb, newdb)
            group = {}
            group['name'] = group_name
            group['netchange'] = 0
            group['status'] = 'gained'
            group['details'] = network_report_data
            group_data.append(group)

        data['groups'] = group_data        
        return data
        
    def write_network_data(self, file):
        '''
        dump the network_diff table 
        '''
        
        query = "select * from network_diff;"
        self.write_report_data(query, file)
