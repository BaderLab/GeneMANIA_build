#!/usr/bin/env perl

use Bio::EnsEMBL::Registry;
use Bio::SeqIO;
use Switch;
use IO::Handle;
use File::Path qw(mkpath); 

use strict;
use warnings;

#_____[global variables]_______________________________________________________

#my $ENSEMBL_VERSION = "65";
#my $ENSEMBL_VERSION = "74";     # use for E. coli
#my $ENSEMBL_VERSION = "77";
#my $ENSEMBL_VERSION = "95";

#my $DB_HOST = "server2.baderlab.med.utoronto.ca";
#my $DB_USER = "mirror";
#my $DB_PASS = "mirror";

#default parameters
my $DB_HOST = "127.0.0.1"; 
my $DB_PORT = "3306";
my $DB_USER = "root";
my $DB_PASS = "gm.build";
my $ENSEMBL_VERSION = "97";

#my $DB_HOST = "ensembldb.ensembl.org";
#my $DB_USER = "anonymous";
#my $DB_PASS = "";


#_____[functions]______________________________________________________________

sub usage {
	print "usage: get_domains.pl db.cfg [all|pfam|smart|superfam|pfscan|scanprosite] savedir\n"; 
}

# grabs protein domains for each logic name for each gene in our organism and writes them to a file.
sub get_protein_domains {
	my $organism = shift;
	my $logic_name = shift; 
	
	print "host:" . $DB_HOST . "user:" . $DB_USER . "pass:" . $DB_PASS . "port:" . $DB_PORT . "\n";
	# connect to the db now 	
	my $registry = 'Bio::EnsEMBL::Registry';
	my $ret = $registry->load_registry_from_db(
	"-host"       => $DB_HOST,
	"-user"       => $DB_USER,
	"-pass"       => $DB_PASS,
	"-port"       => $DB_PORT,
	"-db_version" => $ENSEMBL_VERSION, 
	"-verbose"    => "0"
	);

	my $translation_adaptor = $registry->get_adaptor($organism, "Core", "Translation");
	my $transcript_adaptor = $registry->get_adaptor($organism, 'Core', 'Transcript');

	# get all gene IDs for the organism we want. Use gene_adaptor to obtain a 
	# list of the gene IDs (stable_ids)
	my $gene_adaptor = $registry->get_adaptor($organism, 'Core', 'Gene');
	my @stable_ids   = @{$gene_adaptor->list_stable_ids()};

	my %results_hash = ();

	foreach my $stable_id (@stable_ids) {
		my $gene = $gene_adaptor->fetch_by_stable_id($stable_id);
		#print "Gene: $gene\n"; 
		
		my @transcripts = @{$gene->get_all_Transcripts};
		#print "Transcripts: " . @transcripts . "\n";
		
		foreach my $transcript (@transcripts) {
			#print "got transcript: $transcript\n";
			#print "stable id: " . $transcript->stable_id() . "\n";
			
			my $translation = $transcript->translation();
			if (defined $translation) {
				#print "translation: $translation\n"; 
				
				my @domain_features = @{ $translation->get_all_DomainFeatures };
				foreach my $domain_feature (@domain_features) {
					#print "Logic name: " . $domain_feature->analysis()->logic_name() . + "\n";
					#print "Interpro: " . $domain_feature->interpro_ac() . + "\n";
				
					# get the logic name
					my $lname = lc($domain_feature->analysis()->logic_name());
				
					# get the interpro accession id
					my $ipro = $domain_feature->interpro_ac();
					my $seqname = $domain_feature->hseqname();

					# if the user is looking for a specific domains only, then check to see if this 
					# domain feature is available
					if (lc($logic_name) ne "all") {
						if (lc($logic_name) ne $lname) {
							next;
						}
					}
					
					# check if we already have this stable_id as a key in our hash
					if (exists $results_hash{$stable_id}) {
						# if yes, append this domain ID to the key only if it doesn't already exist					
						if (index($results_hash{$stable_id}, $ipro) == -1) {
							$results_hash{$stable_id} = $results_hash{$stable_id} . "\t$ipro";
						}
					} else {
						if (length($ipro) > 1) {
							$results_hash{$stable_id} = "$stable_id\t$ipro";
						}
					}
				}
			}
		}
		if (exists $results_hash{$stable_id}) {
			#print $results_hash{$stable_id} . "\n";
			print OUT_FILE $results_hash{$stable_id} . "\n";
		}
	}
	close(OUT_FILE);
}


#_____[main starts here]_______________________________________________________

if ( $#ARGV != 2 ) {
	usage();
	exit(0);
}

my $logic_name = $ARGV[1];
my $organism = "";
my $output = ""; 

my $registry = 'Bio::EnsEMBL::Registry';
#my $ret      = $registry->load_registry_from_db(
#	"-host"       => $DB_HOST,
#	"-user"       => $DB_USER,
#	"-pass"       => $DB_PASS,
#	"-port"       => $DB_PORT,
#	"-db_version" => $ENSEMBL_VERSION, 
#	"-verbose"    => "1"
#);
my $ret;

open CFG_FILE, $ARGV[0] or die $1; 
print "Opened config " . $ARGV[0] . "\n"; 

while (<CFG_FILE>) {
       #look for database username and password and ensembl version in the config file
	if($_ =~ m/^ensembl_core_release/){
		my @tmp = split(/=/, $_);
		chomp $tmp[1];
		$tmp[1] =~ s/^\s+//;
		$ENSEMBL_VERSION = $tmp[1];
		#print "ensembl version:" . $ENSEMBL_VERSION . "\n";	
	}

       	#look for login info
       	if($_ =~ m/^mysql_h/){
	       	my @tmp = split(/=/, $_);
	       	chomp $tmp[1];
       		$tmp[1] =~ s/^\s+//;
		$DB_HOST = $tmp[1]; 
		#print "host:" . $DB_HOST . "\n"; 	
	}

       	if($_ =~ m/^mysql_u/){
	       	my @tmp = split(/=/, $_);
	       	chomp $tmp[1];
       	       	$tmp[1] =~ s/^\s+//;
		$DB_USER = $tmp[1]; 
		#print "user:" . $DB_USER . "\n";
	}

      	if($_ =~ m/^mysql_p/){
	       	my @tmp = split(/=/, $_);
	       	chomp $tmp[1];
		$tmp[1] =~ s/^\s+//;
       	       	$DB_PASS = $tmp[1]; 
      		
	
 	}

	# look for spdspecies in db.cfg
	if ($_ =~ m/^spd_org/) {
		my @tmp = split(/=/, $_);
		my @organisms = split(/ /, $tmp[1]); 
		chomp(@organisms); 

		# get data for all the organisms listed under spdspecies
		foreach (@organisms) {
			if (length($_) == 0) {
				next;
			}
		
			$organism = $_;
			chomp($organism);

			# create the directories to store the organism data
			my $save_dir = $ARGV[2] . "/" . $organism . "/raw"; 
			mkpath($save_dir);

			# the output file which gets saved in the directory we just created
			$output = $save_dir . "/" . $ARGV[1] . ".txt"; 
			open OUT_FILE, ">$output"; 
			OUT_FILE->autoflush(1);

			print "Opened output " . $output . "\n"; 
			print "Getting data for " . $organism . "\n"; 

			get_protein_domains( $organism, $logic_name );
		}
	}
}
