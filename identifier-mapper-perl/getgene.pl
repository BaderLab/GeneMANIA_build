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

my $ENSEMBL_VERSION = "85";

my $DB_HOST = "127.0.0.1"; 
my $DB_USER = "root";
my $DB_PASS = 'gm.build';  

my $organism = shift;
my $ensid = shift; 
my $output = ""; 

my $registry = 'Bio::EnsEMBL::Registry';
my $ret      = $registry->load_registry_from_db(
	"-host"       => $DB_HOST,
	"-user"       => $DB_USER,
	"-pass"       => $DB_PASS,
	"-db_version" => $ENSEMBL_VERSION, 
	"-verbose"    => "1"
);

my $translation_adaptor = $registry->get_adaptor($organism, "Core", "Translation");
my $transcript_adaptor = $registry->get_adaptor($organism, 'Core', 'Transcript');
my $gene_adaptor = $registry->get_adaptor($organism, 'Core', 'Gene');
my $dbentry_adaptor = $registry->get_adaptor($organism, 'Core', 'DbEntry');


# start
my $gene = $gene_adaptor->fetch_by_stable_id($ensid); 
print "[+] gene_adaptor: $gene_adaptor\n"; 
print "[+] gene: $gene\n"; 

my $xref_list = $gene->get_all_xrefs(); 
print "[+] xref_list: $xref_list\n"; 


print Dumper \$xref_list; 


print "[+] script completed\n";
