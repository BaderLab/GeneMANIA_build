#!/usr/bin/env perl

use Data::Dumper; 
use Bio::EnsEMBL::Registry;
use Bio::SeqIO;
use feature qw(switch);
use IO::Handle;
use File::Path qw(mkpath); 

use strict;
use warnings;
use syntax "junction";


#_____[global variables]_______________________________________________________

#my $ENSEMBL_VERSION = "95"; # I don't think this is important. To make script useable without any modification should get rid of this parameter. Will only be important when there are multiple versions of ensembl by when using dockerized version theoretically there should just be the latest version.

my $DB_HOST = "127.0.0.1";
my $DB_USER = "root";     # you need to change this if it differs from default
my $DB_PASS = 'gm.build'; # you need to change this if it differs from default

my $savedir = shift; 
my $organism = shift; 
my $short_organism = shift; 
my $num = shift; 

my $output = ""; 

my $registry = 'Bio::EnsEMBL::Registry';
my $ret      = $registry->load_registry_from_db(
	"-host"       => $DB_HOST,
	"-user"       => $DB_USER,
	"-pass"       => $DB_PASS,
#	"-db_version" => $ENSEMBL_VERSION, 
	"-verbose"    => "1"
);

# these are the IDs we want from the external references
my @want_ids = qw(
	EntrezGene
	Uniprot/SWISSPROT
	RefSeq_mRNA
	RefSeq_peptide
);

my $translation_adaptor = $registry->get_adaptor($organism, "Core", "Translation");
my $transcript_adaptor = $registry->get_adaptor($organism, 'Core', 'Transcript');
my $gene_adaptor = $registry->get_adaptor($organism, 'Core', 'Gene');
my $dbentry_adaptor = $registry->get_adaptor($organism, 'Core', 'DbEntry');

my @stable_ids = @{$gene_adaptor->list_stable_ids()};

print "[+] Creating mapping for $organism in ENSEMBL_ENTREZ_$short_organism\n";

# create mapping file 
my $file = $savedir . "/" . "ENSEMBL_ENTREZ_" . $short_organism; 
open(OUT, ">", $file) or die "[!] could not open $file for writing\n"; 

# print file headers
print OUT "GMID\tEnsembl Gene ID\tProtein Coding\tGene Name\tEnsembl Transcript ID\tEnsembl Protein ID\t"; 
print OUT "Uniprot ID\tEntrez Gene ID\tRefSeq mRNA ID\tRefSeq Protein ID\tSynonyms\tDefinition\t"; 

# add MGI ID for mouse
if ($organism eq "mus_musculus") {
	print OUT "MGI ID\t";
}

# add FlyBaseName Gene for fly
if ($organism eq "drosophila_melanogaster") {
	print OUT "FlyBaseName Gene\t";
}

print OUT "\n";

# generate a random GeneMANIA ID and increment it for each gene
my $random_n = int(rand(100000) + ($num * 100000)); 
my $x = 0; 
my $num_missing_genenames = 0;

foreach my $id (@stable_ids) {	
	my $gene = $gene_adaptor->fetch_by_stable_id($id); 
	my @transcripts = @{$gene->get_all_Transcripts()};
	my $transcript_id = undef;  
	foreach my $tid (@transcripts) {
		if (defined $transcript_id) {
			$transcript_id = $transcript_id . ";" . $tid->stable_id(); 			
		} else {
			$transcript_id = $tid->stable_id(); 	
		}
	}
	
	my $protein_id = undef; 
	foreach my $tid (@transcripts) {
		my $translation = $tid->translation(); 
		if (defined $translation) {
			if (defined $protein_id) {
				$protein_id = $protein_id . ";" . $translation->stable_id(); 
			} else {
				$protein_id = $translation->stable_id(); 
			}
		}
	}

	
	my @xref_list = $gene->get_all_xrefs(); 
	my @obj_xref_list = $gene->get_all_object_xrefs(); 
	my @xdb_list = @{$xref_list[0]}; 
	
	my $gmid = undef; 
	my $ensembl_gene_id = undef; 
	my $protein_coding = undef; 
	my $gene_name = undef; 
	my $ensembl_transcript_id = undef; 
	my $ensembl_protein_id = undef; 
	my $uniprot_id = undef; 
	my $mgi_id = undef; 
	my $entrez_gene_id = undef; 
	my $refseq_mrna_id = undef; 
	my $refseq_protein_id = undef;
	my $synonyms = undef; 
	my $definition = undef; 
	my $flybasename_gene = undef; 

	if (defined $gmid) { 
		$gmid += 1; 
	} else {
		$gmid = $random_n + 1; 
		$random_n += 1; 
	}
	
	# Ensembl Gene ID
	$ensembl_gene_id = $id; 

	# Ensembl Transcript ID
	$ensembl_transcript_id = $transcript_id; 

	# Ensembl Protein ID
	$ensembl_protein_id = $protein_id; 
	
	# Protein Coding
	$protein_coding = "\t"; 
	if (defined $gene->biotype) {
		$protein_coding = $gene->biotype; 
	}
	
	# Gene Description
	$definition = $gene->description; 
	
	my $dbentry = $dbentry_adaptor->fetch_by_dbID($gene->dbID);
	my $display_xref = $gene->display_xref; 
	if (defined $display_xref) {
		# Gene Name
		$gene_name = $display_xref->display_id; 
		
		# Synonyms
		my $all_synonyms = $display_xref->get_all_synonyms();
		if (defined $all_synonyms) {
			foreach my $syn (@$all_synonyms) {
				if (defined $syn) {
					# for some reason synonyms are enclosed in single quotes so 
					# we need to remove them
					if ($syn =~ /^['"](.*?)['"]$/) {
						$syn =~ s/^['"](.*?)['"]$/$1/s;
					}
		
					if (defined $synonyms) {
						$synonyms = $syn . ";" . $synonyms;
					} else {
						$synonyms = $syn;
					}
				}
			}
		} else {
			$synonyms = "N/A"; 
		}
	}

	foreach my $xdb (@xdb_list) {
		my $dbname = $xdb->dbname;
		my $realname = "";

		my $noquotes = $xdb->primary_id ;

		given ($dbname) {
			when ("EntrezGene") {
				if (defined $entrez_gene_id) { 
					$entrez_gene_id = $entrez_gene_id . ";" . $xdb->primary_id;
				} else {
					$entrez_gene_id = $xdb->primary_id; 
				}
			}
			
			when (/Uniprot/) {
				if (defined $uniprot_id) { 
					$uniprot_id = $uniprot_id . ";" . $xdb->primary_id  if $uniprot_id !~ /$xdb->primary_id/;
				} else {
					$uniprot_id = $xdb->primary_id  ;				}
			}
			
			when ("Uniprot/SWISSPROT") {
				if (defined $uniprot_id) { 
					$uniprot_id = $uniprot_id . ";" . $xdb->primary_id  if $uniprot_id !~ /$xdb->primary_id/;
				} else {
					$uniprot_id = $xdb->primary_id  ;				}
			}
			when ("Uniprot_gn") {
				if (defined $uniprot_id) { 
					$uniprot_id = $uniprot_id . ";" . $xdb->primary_id  if $uniprot_id !~ /$xdb->primary_id/;
				} else {
					$uniprot_id = $xdb->primary_id  ;				}
			}
			when ("Uniprot_gn") {
				if (defined $uniprot_id) { 
					$uniprot_id = $uniprot_id . ";" . $xdb->primary_id if $uniprot_id !~ /$xdb->primary_id/;
				} else {
					$uniprot_id = $xdb->primary_id  ; 
				}
			}

			when ("Uniprot/SPTREMBL") {
				if (defined $uniprot_id) { 
					$uniprot_id = $uniprot_id . ";" . $xdb->primary_id  if $uniprot_id !~ /$xdb->primary_id/;
				} else {
					$uniprot_id = $xdb->primary_id  ;
				}
			}
			when ("UniProtKB_all") {
				if (defined $uniprot_id) { 
					$uniprot_id = $uniprot_id . ";" . $xdb->primary_id  if $uniprot_id !~ /$xdb->primary_id/ ;
				} else {
					$uniprot_id = $xdb->primary_id  ;
				}
			}
			when ("RefSeq_mRNA") {
				if (defined $refseq_mrna_id) { 
					$refseq_mrna_id = $refseq_mrna_id . ";" . $xdb->primary_id;
				} else {
					$refseq_mrna_id = $xdb->primary_id; 
				}
			}
			when ("RefSeq_peptide") {
				if (defined $refseq_protein_id) { 
					$refseq_protein_id = $refseq_protein_id . ";" . $xdb->primary_id;
				} else {
					$refseq_protein_id = $xdb->primary_id; 
				}
			}
			when ("MGI") {
				if (! defined $mgi_id)  {
					$mgi_id = $xdb->primary_id; 
				}
			}
			when("FlyBaseName_gene") {
				if (! defined $flybasename_gene) {
					if( defined $xdb->description){
						my @fbname = split(/ /, $xdb->description); 
						if (scalar @fbname < 3) {
							foreach (@fbname) {
								$flybasename_gene .= $_ . " ";
							}
						}
						else {
							$flybasename_gene = "N/A";
						}
					} else {
						$flybasename_gene = "N/A";
					}
				}
			}
		}
	}

	#print "---------------------------------------------------------------------------------\n"; 
	#print "gmid: [$gmid]\n";
	#print "ensembl gene id: [$ensembl_gene_id]\n";
	#print "ensembl transcript id: [$ensembl_transcript_id]\n";
	#print "ensembl protein id: [$ensembl_protein_id]\n";
	#print "protein coding: [$protein_coding]\n"; 
	#print "uniprot id: [$uniprot_id]\n";
	#if ($organism eq "mus_musculus") {
	#	print "mgi id: [$mgi_id]\n";
	#}
	#print "gene name: [$gene_name]\n"; 
	#print "entrez gene id: [$entrez_gene_id]\n"; 
	#print "refseq mrna id: [$refseq_mrna_id]\n"; 
	#print "refseq protein id: [$refseq_protein_id]\n"; 
	#print "synonyms: [$synonyms]\n"; 
	#print "definition: [$definition]\n"; 

	# mark a field as N/A if it's empty
	if (! defined $uniprot_id) { $uniprot_id = "N/A"; } 
	if (! defined $mgi_id) { $mgi_id = "N/A"; } 
	if (! defined $entrez_gene_id) { $entrez_gene_id = "N/A"; } 
	if (! defined $refseq_mrna_id) { $refseq_mrna_id = "N/A"; } 
	if (! defined $refseq_protein_id) { $refseq_protein_id = "N/A"; } 
	if (! defined $synonyms) { $synonyms = "N/A"; } 
        # add blank for defintion to get rid of warning
	if (! defined $ensembl_protein_id ) { $ensembl_protein_id = "N/A"; }
	if (! defined $definition) { $definition = "N/A"; }

	#there are also a few warnings coming up that gene_name is also blank
	if (! defined $gene_name) {
		$gene_name = "N/A";
		$num_missing_genenames+= 1;
	}

	# save results to mapping file
	print OUT "$gmid\t$ensembl_gene_id\t$protein_coding\t$gene_name\t" .
		"$ensembl_transcript_id\t$ensembl_protein_id\t$uniprot_id\t"; 

	print OUT "$entrez_gene_id\t$refseq_mrna_id\t$refseq_protein_id\t" .
		"$synonyms\t$definition\t";	
			
	# record MGI ID if mouse
	if ($organism eq "mus_musculus") {
		print OUT "$mgi_id\t"; 
	}
	
	# record FlyBaseName Gene if fly
	if ($organism eq "drosophila_melanogaster") {
		print OUT "$flybasename_gene";
	}
	
	print OUT "\n";
}

print "[+] $organism script completed\n";

my $file2 = $savedir . "/" .  $short_organism . "_done.txt"; 
open(OUT2, ">", $file2) or die "[!] could not open $file for writing\n";
print OUT2 "There were $num_missing_genenames records with missing gene_names\n";
print OUT2 "[+] $organism script completed\n";
