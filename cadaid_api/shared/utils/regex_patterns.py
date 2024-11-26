#scale_pattern = r'\b(?:Målestokk|Malestok|[Mm]ål|[Ss]cale)\s*[1:]\s*:\s*\d+(?:\s*:\s*\d+)?\b'
scale_pattern = r'\b(?:Målestokk|Malestokk)?\s*(\d+):(\d+)\b'
#scale_pattern = r"\d+\s*:\s*\d+"
#cardinal_direction_pattern = r'\b(?:sør|vest|nord|øst|[NSØV](?:\s*)|[Nn]ord-?[ØøVv]est|[Ss]ør-?[ØøVv]est)'
cardinal_direction_pattern = r'\b(?:nord(?:vest|øst)?|sør(?:vest|øst)?|øst|vest)\b'
room_pattern = r'\b(?:[Ss]ov(?:erom)?(?:\s*\d+)?|[Gg]ang|[Bb]od(?:er)?|[Bb]ad(?:erom)?|[Kk]jøkken|[Tt]rapp(?:erom)?|[Ss]tue|[Kk]ontor|[Ee]ntr[eé]|[Gg]arasje|[Tt]rappegang|[Tt]errasse|[Kk]ott|[Ss]al|[Uu]tvendig|[Cc]arport|[Vv]ask(?:erom)?|[Gg]rovinngang|[Mm]atbod|[Ww]alk-[Ii]n|[Hh]all|[Tt]rimrom|[Ww][Cc]|[Bb]alkong)(?:\s[-/]\s(?:[Ss]tue|[Kk]jøkken|[Bb]od))?\b(?:\s(?:\d+(?:[.,]\d+)?)\sm²)?'
#gnr_bnr_pattern = r'\b(?:G(?:år)?(?:ds)?(?:nr)?(?:nummer)?.?\s(\d+)\s/\sB(?:ruks)?(?:nr)?(?:nummer)?.?\s(\d+))|(?:\b(?:(?:G|g)nr.?/(?:B|b)nr.?\s*)?(\d+)/(\d+)\b)'
areal_pattern = r"\b\d+(\.\d+)?\s?(?:m2|kvadrat\s?meter?|m\b|)\b"

#New simplified gnr/bnr pattern to match the format:
gnr_bnr_pattern = r'\b(?:(?:(?:G|g)nr.?/(?:B|b)nr.?(?:/[Ff]estenr.?)?[:.]?\s(\d+)/(\d+))|(?:g.?n.?/\sb.?nr.?\s(\d+)/(\d+))|(?:GBNR\s(\d+)-(\d+))|(?:\b(\d+)/(\d+)\b)|(?:(?:G|g)nr.?:?\s(\d+)\s(?:\n|\r\n)?(?:(?:B|b)nr.?:?\s(\d+)))|(?:(?:B|b)nr.?:?\s(\d+)\s(?:\n|\r\n)?(?:(?:G|g)nr.?:?\s(\d+))))\b'

#New scale pattern to better handle the format:
#scale_pattern = r'\b(?:Målestokk|Malestokk|[Mm]ål|[Ss]cale)?\s[1:]?\s:\s\d+(?:\s:\s\d+)?\b'