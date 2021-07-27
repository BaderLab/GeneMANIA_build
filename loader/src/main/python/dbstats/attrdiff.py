'''
mostly a cut&paste of the network diff, when instead of thinking of all
the attributes forming a group, think of each attribute 'set' such as interpro
as a group and each attribute within the set as a network
'''

import utils

class AttributesDiff(utils.Db):
    
    def __init__(self, conn, org_name):
        self.conn = conn
        self.org_name = org_name

    def createDiffTable(self):
        '''temporary reporting table'''
        
        
        # status is 'added', 'removed', or 'maintained'
        sql = '''
        drop table if exists attributes_diff;
        
        create temp table attributes_diff (Attribute_Group_Name text, Attribute_Name text, 
        status text,
        old_id int, new_id int, 
        old_num_nodes int, new_num_nodes int,
        nodes_lost int, nodes_gained int);
        
        create index ix_attributes_diff on attributes_diff (Attribute_Group_Name, Attribute_Name);         
        '''
        
        self.executescript(sql)
        
    def diffGroups(self, olddb = "old", newdb = "new"):
        '''
        determine attribute groups lost, maintained, and gained between two releases, 
        comparing by group name
        '''
                
        if not olddb and not newdb:
            raise Exception("can't compare nothing to noone!")
        
        groupsLost = groupsMaintained = groupsGained = []
        
        if not olddb:
            groupsSql = "SELECT distinct(Attribute_Group_Name) from %s.attributes;"  
            sql = groupsSql % (newdb)
            results = self.select(sql)
            
            groupsGained = [result[0] for result in results]
            
            
        elif not newdb:
            groupsSql = "SELECT distinct(Attribute_Group_Name) from %s.attributes;"  
            sql = groupsSql % (olddb)
            results = self.select(sql)
            
            groupsLost = [result[0] for result in results]
            
        else:
            
            # gained
            groupDiffSql = "SELECT distinct(Attribute_Group_Name) from %s.attributes where Attribute_Group_Name not in (select distinct(Attribute_Group_Name) from %s.attributes)" 
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
            groupOverlapSql = "SELECT distinct(Attribute_Group_Name) from %s.attributes where Attribute_Group_Name in (select distinct(Attribute_Group_Name) from %s.attributes) order by Attribute_Group_Name"
            sql = groupOverlapSql % (olddb, newdb)
            results = self.select(sql)
            groupsMaintained = [result[0] for result in results]
            print(str(groupsMaintained)[1:-1])
        
        return groupsLost, groupsMaintained, groupsGained

    def diffAttributes(self, olddb = "old", newdb = "new"):
        '''
        results in table 'attributes_diff'
        '''
        
        self.createDiffTable()
        
        if not olddb and not newdb:
            raise Exception("can't compare nothing to noone!")
        
        attributeGainSql = """
        INSERT INTO attributes_diff (attribute_group_name, attribute_name, status, 
        new_id, new_num_nodes)
        SELECT t1.Attribute_Group_Name, t1.Attribute_Name, '%s',
        t1.attribute_id, t1.num_nodes
        from %s.attributes as t1;
        """

        attributeLostSql = """
        INSERT INTO attributes_diff (attribute_group_name, attribute_name, status, 
        old_id, old_num_nodes)
        SELECT t1.Attribute_Group_Name, t1.Attribute_Name, '%s',
        t1.attribute_id, t1.num_nodes 
        from %s.attributes as t1;
        """
        
        if not olddb:            
            sql = attributeGainSql % ('added', newdb)
            self.execute(sql)
                                
        elif not newdb:            
            sql = attributeLostSql % ('removed', olddb)
            self.execute(sql)
        
        else:
       
            # note the sql here matches by both group and attribute name, since possibly the same
            # attribute name can be used in a different group. 
            attributeGainSql = """
            INSERT INTO attributes_diff (attribute_group_name, attribute_name, status, 
            new_id, new_num_nodes)
            SELECT t1.Attribute_Group_Name, t1.Attribute_Name, '%s',
            t1.attribute_id, t1.num_nodes
            from %s.attributes as t1 where not exists 
               (SELECT t2.Attribute_Group_Name, t2.Attribute_Name from %s.attributes as t2 
                where t1.Attribute_Group_Name = t2.Attribute_Group_Name 
                and t1.Attribute_Name = t2.Attribute_Name);
            """

            attributeLostSql = """
            INSERT INTO attributes_diff (attribute_group_name, attribute_name, status, 
            old_id, old_num_nodes)
            SELECT t1.Attribute_Group_Name, t1.Attribute_Name, '%s',
            t1.attribute_id, t1.num_nodes 
            from %s.attributes as t1 where not exists 
               (SELECT t2.Attribute_Group_Name, t2.Attribute_Name from %s.attributes as t2 
                where t1.Attribute_Group_Name = t2.Attribute_Group_Name 
                and t1.Attribute_Name = t2.Attribute_Name);
            """
            
            sql = attributeGainSql % ('added', newdb, olddb)
            self.execute(sql)
            
            sql = attributeLostSql % ('removed', olddb, newdb)
            self.execute(sql)
                        
            # determine matches and build into list for analysis
            attributeMatchSql = """
            INSERT INTO attributes_diff (Attribute_Group_Name, Attribute_Name, status,
            old_id, new_id, old_num_nodes, new_num_nodes) 
            SELECT t1.Attribute_Group_Name, t1.Attribute_Name, 'maintained', 
               t1.Attribute_Id as old_id, t2.Attribute_Id as new_id,
               t1.Num_Nodes as old_num_nodes, t2.Num_Nodes as new_num_nodes
            from %s.attributes as t1, %s.attributes as t2 
            where t1.Attribute_Group_Name = t2.Attribute_Group_Name
            and t1.Attribute_Name = t2.Attribute_Name
            """
    
            sql = attributeMatchSql % (olddb, newdb)
            self.execute(sql)
            attributesMaintained = self.select("select * from attributes_diff;")
            print("maintained: " + str(attributesMaintained)[1:-1])
   
    def createAttributeGroupReportData(self, group_name, olddb = "old", newdb = "new"):
        '''
        return a dictionary containing data to
        be interpolated into the report template
        
        the diff data should be generated in the attributes_diff table.        
        '''
        
        if not olddb and not newdb:
            raise Exception("can't compare nothing to noone!")
                
        d = {}
        d['Group'] = group_name

        d['maintained'] = self.select("select rowid, * from attributes_diff where status = 'maintained' and Attribute_Group_Name = '%s'" % group_name)
        d['gained'] = self.select("select rowid, * from attributes_diff where status = 'added' and Attribute_Group_Name = '%s'" % group_name)
        d['lost'] = self.select("select rowid, * from attributes_diff where status = 'removed' and Attribute_Group_Name = '%s'" % group_name)
        d['old_num_attributes'] = 0        
        d['new_num_attributes'] = 0
        d['sample_nodes_lost'] = []
        d['sample_nodes_added'] = []
                    
        if olddb:        
            d['old_num_attributes'] = self.selectNumber("select count(*) from old.attributes where Attribute_Group_Name = '%s'" % group_name)
            
        if newdb:
            d['new_num_attributes'] = self.selectNumber("select count(*) from new.attributes where Attribute_Group_Name = '%s'" % group_name)
         
        return d
                   
    def diff(self, olddb = "old", newdb = "new"):
        '''
        return a dictionary containing report data by querying
        stats db
        '''
                
        groups_lost, groups_maintained, groups_gained = self.diffGroups(olddb, newdb)
        self.diffAttributes(olddb, newdb)
 
        data = {}
        data['name'] = self.org_name
 
        group_data = []
        for group_name in groups_maintained:
            attribute_report_data = self.createAttributeGroupReportData(group_name, olddb, newdb)
            attribute_report_data['width'] = 50*len(attribute_report_data['maintained'])
            group = {}
            group['name'] = group_name
            group['netchange'] = attribute_report_data['new_num_attributes']- attribute_report_data['old_num_attributes']
            group['status'] = 'maintained'
            group['details'] = attribute_report_data
            group_data.append(group)

        for group_name in groups_lost:
            attribute_report_data = self.createAttributeGroupReportData(group_name, olddb, newdb)
            group = {}
            group['name'] = group_name
            group['netchange'] = 0
            group['status'] = 'lost'
            group['details'] = attribute_report_data
            group_data.append(group)

        for group_name in groups_gained:
            attribute_report_data = self.createAttributeGroupReportData(group_name, olddb, newdb)
            group = {}
            group['name'] = group_name
            group['netchange'] = 0
            group['status'] = 'gained'
            group['details'] = attribute_report_data
            group_data.append(group)

        data['groups'] = group_data        
        return data
