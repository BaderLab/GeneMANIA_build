#!/usr/bin/env python
import sys, os, re
from check_mapping import CheckMapping

def get_gene_id(field, check, no_mapping, gene_id):
	aliases = field.split("|")
	print "aliases for %s: %s" % (gene_id, aliases)
	for alias in aliases: 
		if alias == "-":
			continue

		print "searching id mapping for", alias
		gene = alias.split(":")[1]
		if check.has_mapping(gene):
			print "using gene %s for %s" % (gene, gene_id)
			return gene
		else:
			no_mapping[gene] = 1

	print "no mapping found for", gene_id
	return None


def make_interactions(rawfile, outdir, mappings_dir, mapping_file, columns):
	interactions = {}	# used to check for interaction duplicates
	no_mapping = {}		# contains genes we have no mappings for
	by_pmid = {}		# interactions with pubmed IDs
	by_source = {}		# interactions with source only
	threshold = 100

	check = CheckMapping(os.path.join(mappings_dir,  mapping_file))
	if not os.path.exists(outdir):
		os.mkdir(outdir)

	#nopmid = open(os.path.join(outdir, "no_pmid.txt"), "w")
	print ""

	skipped_header = False
	for line in open(rawfile):
		if not skipped_header:
			skipped_header = True
			continue

		line = line.strip()
		fields = line.split("\t")

                # skip the line if it doesn't have source defined.
                if len(fields) < 13:
                    continue

		score = "0"

		# get gene ids
                # some of the sources are coming back empty creating networks called -.txt
                # originally thought that it was just quickgo but there are a few networks like these
                # instead of getting the source from the source identifier column grab it from the sourcedb
                # column which lists an MI term and the associated source.  A bunch of sources are identified
                # with the MI code MI:0000(name of source) so grab the source name from between the brackets.
                source = re.search('\(([^)]+)',fields[12]).group(1);
                #source = fields[13].split(":")[0].upper() if ':' in fields[13] else fields[13].upper()
		print "processing source:", source


		# get the columns:
		col_1 = int(columns.split(",")[0])
		col_2 = int(columns.split(",")[1])

		geneA = get_gene_id(fields[col_1], check, no_mapping, "gene A")
		geneB = get_gene_id(fields[col_2], check, no_mapping, "gene B")

		if geneA == None or geneB == None:
			print "src: geneA or geneB unrecognized for", source
			print "dropping interaction\n"
			continue

		#pmid = "0"
                pmids = []
		if fields[8] != '-':
                        #get rid of the "pubmed:" from the pubmed ids
                        parsed_pmids= fields[8].replace("pubmed:","") if "pubmed:" in fields[8] else fields[8]
                        
                        #There could be multiple pmids in the pubmed column
                        pmids = parsed_pmids.split('|') if '|' in parsed_pmids else [parsed_pmids]
			
                        print("The pmids are:", pmids)
                        # if there's a pubmed ID save it
                        #pmid = fields[8].split(":")[1] if ':' in fields[8] else fields[8]

		itxn_type = fields[11]

		# process source interactions first
		#if pmid == "0":
		if source not in by_source:
			by_source[source] = {"itxn_list":[]}

		# already processed geneA/B and found no mapping for it, skip it
		if geneA in no_mapping or geneB in no_mapping:
			print "src: already found no mapping for %s or %s earlier" % (geneA, geneB)
			print "dropping interaction\n"
			continue

		# check if we have mappings, if not mark it as no mapping found so
		# if we see it again we can skip it
		#if not check.has_mapping(geneA): 
		#	no_mapping[geneA] = 1
		#	print "!!!! no mapping found for geneA %s for %s" % (geneA, source)
		#	continue

		#if not check.has_mapping(geneB):
		#	no_mapping[geneB] = 1
		#	print "!!!! no mapping found for geneB %s for %s" % (geneB, source)
		#	continue

		if geneA == geneB:
			print "src: geneA and geneB %s for %s is identical" % (geneA, source)
			print "dropping interaction\n"
			continue

		# gene gene score, forward and reversed
		s = "%s\t%s\t1" % (geneA, geneB)
		r = "%s\t%s\t1" % (geneB, geneA)

		# skip any duplicates
		dup_s = source + ":" + s
		if dup_s in interactions:
			print "src: %s for %s is already recorded" % (dup_s, source)
			print "dropping interaction\n"
			continue

		dup_r = source + ":" + r
		if dup_r in interactions:
			print "src: %s for %s is already recorded" % (dup_r, source)
			print "dropping interaction\n"
			continue

		# add to iteractions list
		interactions[dup_s] = "1"
		interactions[dup_r] = "1"
		print "src: adding %s to %s" % (s, source)
		by_source[source]["itxn_list"].append(s)

		#else:
		#if pmid != "0":
                if len(pmids) > 0:
                        for pmid in pmids:
                                print "this interaction has PMID", pmid
			        # for interactions with pubmed IDs
			        if pmid not in by_pmid:
				        by_pmid[pmid] = {"itxn_list":[], "is_gi":False}

				        # check if these are genetic interactions
				        if "genetic" in itxn_type:
					        by_pmid[pmid]["is_gi"] = True

			        # already processed geneA/B and found no mapping for it, skip it
			        if geneA in no_mapping or geneB in no_mapping:
				        print "pmid: geneA or geneB unrecognized for", pmid
				        print "dropping interaction\n"
				        continue

			        # check if we have mappings, if not mark it as no mapping found so
			        # if we see it again we can skip it
			        #if not check.has_mapping(geneA): 
			        #	no_mapping[geneA] = 1
			        #	continue

			        #if not check.has_mapping(geneB):
			        #	no_mapping[geneB] = 1
			        #	continue

			        if geneA == geneB:
				        print "pmid: geneA and geneB %s for %s is identical" % (geneA, pmid)
				        print "dropping interaction\n"
				        continue

			        # gene gene score, forward and reversed
			        s = "%s\t%s\t1" % (geneA, geneB)
			        r = "%s\t%s\t1" % (geneB, geneA)

			        # skip any duplicates
			        pmid_s = pmid + ":" + s
			        if pmid_s in interactions:
				        print "pmid: %s for %s is already recorded" % (pmid_s, pmid)
				        print "dropping interaction\n"
				        continue

			        pmid_r = pmid + ":" + r
			        if pmid_r in interactions:
				        print "pmid: %s for %s is already recorded" % (pmid_r, pmid)
				        print "dropping interaction\n"
				        continue

			        # add to iteractions list
			        interactions[pmid_s] = "1"
			        interactions[pmid_r] = "1"

			        print "pmid: adding %s to %s" % (s, pmid)
			        print " "
			        by_pmid[pmid]["itxn_list"].append(s)
		else:
			print "no PMID to process, moving on to next interaction\n"


	# write the good stuff to the files with pubmed ids as file names
	#print "Writing to", os.path.join(outdir)
	for pmid in by_pmid:
		# pubmed id's with >= threshold interactions
		if len(by_pmid[pmid]["itxn_list"]) >= threshold:
			outf = None
			if by_pmid[pmid]["is_gi"]:
				outf = open(os.path.join(outdir, pmid + "_GI.txt"), "w")
			else:
				outf = open(os.path.join(outdir, pmid + ".txt"), "w")
			for interaction in by_pmid[pmid]["itxn_list"]:
				outf.write(interaction + "\n")
			outf.close()
		else:
			# pubmed id's with < threshold interactions get clumped in a
			# single file
			outf = None
			if by_pmid[pmid]["is_gi"]:
				outf = open(os.path.join(outdir, "under_threshold_GI.txt"), "a")
			else:
				outf = open(os.path.join(outdir, "under_threshold.txt"), "a")
			for interaction in by_pmid[pmid]["itxn_list"]:
				outf.write(interaction + "\n")
			outf.close()

	for source in by_source:
		if len(by_source[source]["itxn_list"]) > 0:
			print "writing %s :%d" % (source, len(by_source[source]["itxn_list"]))
			outf = open(os.path.join(outdir, source + ".txt"), "w")
			for interaction in by_source[source]["itxn_list"]:
				outf.write(interaction + "\n")
			outf.close()


def main(argv):
	if len(argv) < 5:
		print "Usage: %s rawfile outdir mapping_dir mapping_file [column1,column2]" % (argv[0])
		print " - By default columns 4,5 are selected. In some cases like E. Coli\n"
		print "   we need to use columns 3,4" 
		sys.exit(0)

	print "Creating interaction file from", argv[1]
	print "Using outdir", argv[2]
	print "Using mapping file %s/%s" % (argv[3], argv[4])

	# check if user provided optional columns
	if len(argv) == 6:
		make_interactions(argv[1], argv[2], argv[3], argv[4], argv[5])
	else:
		make_interactions(argv[1], argv[2], argv[3], argv[4], "4,5")


if __name__ == "__main__":
	main(sys.argv)
