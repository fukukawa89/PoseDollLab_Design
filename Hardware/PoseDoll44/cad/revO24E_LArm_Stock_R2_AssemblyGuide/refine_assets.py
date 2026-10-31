from pathlib import Path
p=Path(__file__).with_name('guide.js');s=p.read_text('utf8');s=s.replace('#section.checked=!!s.auto_section;',"$('#section').checked=!!s.auto_section;")
p.write_text(s,encoding='utf8')
