def canonicalize(instr):
	outt = []
	npos = pos = 0
	while pos <= len(instr):
		npos += 8
		s = instr[pos:npos]
		if not s:
			break
		hs = ''
		cs = ''
		for c in s:
			n = ord(c)
			hs += "%02x" % n
			cs += c if 32<n<127 else '.'
		outt.append((pos,hs, cs))
		pos = npos
	
	#print outt
	outh = outc = ''
	ostr = ["len: %s"%len(instr)]
	eight=sixteen=ppos=0
	state=0
	for pos, h, c in outt:
		outh += "%-16s" %h
		outc += "%-8s" % c
		eight = (pos % 8)==0
		sixteen = (pos % 16)==0

		if state==0:
			ppos = pos
			outh += ' '	
			outc += ' '
			state = 1
		elif state==1:
			ostr.append("%04x: |%s| |%s|" % (ppos, outh, outc))
			outh = outc = ''
			state = 0
		#print pos, eight, sixteen
		#if eight and not sixteen:
		#	outh += ' '	
		#	outc += ' '	
		#if sixteen:
		#	ppos = pos
		#if pos>0 and sixteen:
		#	ostr.append("%04x: |%s| |%s|" % (ppos, outh, outc))
		#	outh = outc = ''
			
		
	#print pos, outc, outh
	#if pos==0 or (eight and not sixteen):
	#if len(outc)<0:
	if len(instr) == 0:
		ostr.append("%04x: |%s| |%s|" % (ppos,  ' '*33, ' '*17))
	elif state == 1:
		ostr.append("%04x: |%s                | |%s        |" % (ppos, outh, outc))
		outh = outc = ''
	return '\n'.join(ostr)

def hexscii(s):
	d=''
	l=len(s)
	p=0
	while p<l:
		e=p+2
		d+=chr(int(s[p:e],16))
		p=e
	return d


if __name__ == '__main__':
	strs = [
		'',
		'a',
		'a'*8,
		'a'*9,
		'a'*16,
		'a'*17,
		'a'*23,
		'a'*24,
		'a'*31,
		'a'*32,
	]

	for s in strs:
		print "==="
		print canonicalize(s)
