from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from marketplace.models import SocialMediaAccount, Category
from django.utils.text import slugify


class Command(BaseCommand):
    """
    Django management command to assign categories to social media accounts.
    
    This command iterates through all SocialMediaAccount instances and:
    1. Creates Category objects for each unique social_media type if they don't exist
    2. Assigns the appropriate category to each social media account
    
    The command is designed to be safe for production use with:
    - Database transactions for data integrity
    - Proper error handling and logging
    - Dry-run option for testing
    - Progress reporting
    """
    
    help = (
        'Assigns categories to social media accounts based on their social_media field. '
        'Creates new Category objects as needed and links them to existing accounts.'
    )
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making any changes to the database',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output of operations',
        )
    
    def handle(self, *args, **options):
        """Main command execution logic."""
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE: No changes will be made to the database')
            )
        
        try:
            # Get all social media accounts
            accounts = SocialMediaAccount.objects.all()
            total_accounts = accounts.count()
            
            if total_accounts == 0:
                self.stdout.write(
                    self.style.WARNING('No social media accounts found in the database.')
                )
                return
            
            self.stdout.write(
                f'Found {total_accounts} social media accounts to process.'
            )
            
            # Track statistics
            categories_created = 0
            accounts_updated = 0
            categories_cache = {}
            
            # Use database transaction for data integrity
            with transaction.atomic():
                for i, account in enumerate(accounts, 1):
                    if verbose:
                        self.stdout.write(
                            f'Processing account {i}/{total_accounts}: {account}'
                        )
                    
                    # Skip if account already has a category assigned
                    if account.category:
                        if verbose:
                            self.stdout.write(
                                f'  Account already has category: {account.category}'
                            )
                        continue
                    
                    # Get or create category
                    social_media_type = account.social_media
                    
                    if not social_media_type:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  Account {account} has no social_media type, skipping'
                            )
                        )
                        continue
                    
                    # Use cache to avoid repeated database queries
                    if social_media_type in categories_cache:
                        category = categories_cache[social_media_type]
                        if verbose:
                            self.stdout.write(
                                f'  Using cached category: {category}'
                            )
                    else:
                        # Try to get existing category
                        try:
                            category = Category.objects.get(name=social_media_type)
                            if verbose:
                                self.stdout.write(
                                    f'  Found existing category: {category}'
                                )
                        except Category.DoesNotExist:
                            # Create new category
                            if not dry_run:
                                category = Category.objects.create(
                                    name=social_media_type,
                                    slug=slugify(social_media_type)
                                )
                                categories_created += 1
                                if verbose:
                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f'  Created new category: {category}'
                                        )
                                    )
                            else:
                                # In dry run, create a mock category object
                                category = Category(name=social_media_type)
                                categories_created += 1
                                if verbose:
                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f'  Would create new category: {social_media_type}'
                                        )
                                    )
                        
                        # Cache the category
                        categories_cache[social_media_type] = category
                    
                    # Assign category to account
                    if not dry_run:
                        account.category = category
                        account.save(update_fields=['category'])
                        accounts_updated += 1
                        if verbose:
                            self.stdout.write(
                                f'  Assigned category {category} to account {account}'
                            )
                    else:
                        accounts_updated += 1
                        if verbose:
                            self.stdout.write(
                                f'  Would assign category {category.name} to account {account}'
                            )
                
                # If dry run, rollback the transaction
                if dry_run:
                    transaction.set_rollback(True)
            
            # Print summary
            self.stdout.write('\n' + '='*50)
            self.stdout.write('SUMMARY:')
            self.stdout.write(f'Total accounts processed: {total_accounts}')
            self.stdout.write(f'Categories created: {categories_created}')
            self.stdout.write(f'Accounts updated: {accounts_updated}')
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('\nDRY RUN COMPLETED - No changes were made')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('\nCOMMAND COMPLETED SUCCESSFULLY')
                )
        
        except Exception as e:
            raise CommandError(f'Command failed with error: {str(e)}')