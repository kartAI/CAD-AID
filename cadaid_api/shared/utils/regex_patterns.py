#scale_pattern = r'\b(?:Målestokk|Malestok|[Mm]ål|[Ss]cale)\s*[1:]\s*:\s*\d+(?:\s*:\s*\d+)?\b'
scale_pattern = r'\b(?:Målestokk|Malestokk)?\s*(\d+):(\d+)\b'
#scale_pattern = r"\d+\s*:\s*\d+"
#cardinal_direction_pattern = r'\b(?:sør|vest|nord|øst|[NSØV](?:\s*)|[Nn]ord-?[ØøVv]est|[Ss]ør-?[ØøVv]est)'
cardinal_direction_pattern = r'\b(?:sør|vest|nord|øst){1,2}\b'
room_pattern = r'\b(?:[Ss]ov(?:erom)?|[Gg]ang|[Bb]od|[Bb]ad(?:erom)?|[Kk]jøkken|[Tt]rapp(?:erom)?|[Ss]tue|[Kk]ontor|[Ee]ntre|[Gg]arasje|[Tt]rappegang|[Tt]errasse|[Kk]ott|[Ss]al|[Uu]tvendig|[Cc]arport)\b(?:\s*(?:\d+(?:[.,]\d+)?)\s*m²)?'
gnr_bnr_pattern = r'\b(?:G(?:år)?(?:ds)?(?:nr)?(?:nummer)?.?\s(\d+)\s/\sB(?:ruks)?(?:nr)?(?:nummer)?.?\s(\d+))|(?:\b(?:(?:G|g)nr.?/(?:B|b)nr.?\s*)?(\d+)/(\d+)\b)'
areal_pattern = r"\b\d+(\.\d+)?\s?(?:m2|kvadrat\s?meter?|m\b|)\b"