import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
import aiohttp
import asyncio
import logging
import async_timeout
import json
import time
import datetime
import math
import subprocess
import aiomysql
import base64
import configparser
from random import randint
from random import seed
import ctypes
import os
import hashlib
import urllib.request
import re
import numpy as np

ctypes.windll.kernel32.SetConsoleTitleW("MotW Challenge Bot - Last Started: "+str(time.strftime("%c")))

bt = str(int(os.path.getmtime(__file__)))
ve = "0." + bt[:2] + "." + bt[2:-4] + "." + bt[-4:]

config = configparser.ConfigParser()
config.read('challenge_motw.cfg')

dis_key = config.get('discord','key')
main_server = config.get('discord','server')

osu_key = config.get('osu','key')
osu_api = "https://osu.ppy.sh/api/"
bot_name = "MotW Challenge Bot"
bot_channel = ""

mysql_host = config.get('mysql','host')
mysql_user = config.get('mysql','username')
mysql_pass = config.get('mysql','password')
mysql_data = config.get('mysql','database')

osu_mods_t = {
	"1":"NF",
	"2":"EZ",
	"8":"HD",
	"16":"HR",
	"32":"SD",
	"64":"DT",
	"128":"RX",
	"256":"HT",
	"512":"NC",
	"1024":"FL",
	"2048":"AP",
	"4096":"SO",
	"8192":"RX",
	"16384":"PF",
	"32768":"4K",
	"65536":"5K",
	"131072":"6K",
	"262144":"7K",
	"524288":"8K",
	"1048576":"FI",
	"2097152":"RD",
	"16777216":"9K",
	"67108864":"1K",
	"134217728":"3K",
	"268435456":"2K"
	}

bc_api = "http://bloodcat.com/osu/?mod=json&s=1"

def log(log :str):
	print("[" + str(time.strftime("%d/%m/%Y-%H:%M:%S")) + "] " + log)

def GetMods(x):
	return [(1<<i) for i in range(0,25) if int(x) & (1<<i)]

def correct_channel(channel_id):
	if channel_id == bot_channel:
		return 1
	else:
		return 0

def gen_embed(co,se,me):
	te = discord.Embed(colour=discord.Colour(co), description=me)
	te.set_author(name=se.name)
	return te

def Ordinal(x):
	return "%d%s" % (x,"tsnrhtdd"[(math.floor(x/10)%10!=1)*(x%10<4)*x%10::4])


bot = commands.Bot(command_prefix='=', description='MotW Challenge Bot by TheMeq\r\n\r\nVersion '+str(ve), pm_help= True)

@bot.event
async def on_ready():
	_=os.system("cls")
	print(r"")
	print(r" MotW Challenge Bot by TheMeq")
	print(r"")
	print(r" Version "+ve)
	print(r" Timestamp "+str(datetime.datetime.fromtimestamp(int(bt)).strftime("%d/%m/%Y-%H:%M:%S")))
	print(r"")
	log("Logged in as: " + bot.user.id + " ("+ bot.user.name+")")
	log("Setting Discord game presence to \"osu! (=help)\"")
	await bot.change_presence(game=discord.Game(name='osu! (=help)'))

def getBounty(v:int):
	m = (360-v)/60
	o = (10 * m**2)
	if v >= 0 and v< 60:
		o = o * 1.6
	if v >= 60 and v < 120:
		o = o * 1.5
	if v >= 120 and v < 180:
		o = o * 1.4
	if v >= 180 and v < 240:
		o = o * 1.3
	if v >= 240 and v < 300:
		o = o * 1.2
	t= 10 + o
	return int(t)
	
def olembed(colour,text):
	embed = discord.Embed(colour=discord.Colour(colour), description=text)
	return embed

async def getchallenge():
	log("--------------------------------")
	log("-- Getting A New Challenge... --")
	log("--------------------------------")
	mysql_conn = await aiomysql.connect(host= mysql_host, port= 3306, user= mysql_user, password= mysql_pass, db= mysql_data)
	mysql_curs = await mysql_conn.cursor()
	mysql_quer = "SELECT COUNT(*) as TOTAL FROM challenge WHERE winner = 0"
	await mysql_curs.execute(mysql_quer)
	challenges_count = await mysql_curs.fetchone()
	log("> Current Challenge count: "+str(challenges_count[0]))
	if challenges_count[0] >= 10:
		log("> Challenge count greater than 10. Skipping.")
		text = "Not creating a new challenge as there were more than 10 challenges."
	else:
		mysql_quer = "SELECT COUNT(*) AS TOTAL FROM challenge_bm WHERE MODE = 0"
		await mysql_curs.execute(mysql_quer)
		total_beatmaps = await mysql_curs.fetchone()
		log("> Choosing from "+str(total_beatmaps[0])+" beatmaps...")
		r_beatmap_id = np.random.randint(0,total_beatmaps[0]-1)
		mysql_quer = "SELECT BEATMAP_ID FROM challenge_bm WHERE MODE = 0 LIMIT " + str(r_beatmap_id) + ",1"
		await mysql_curs.execute(mysql_quer)
		get_beatmapid = await mysql_curs.fetchone()
		r_selected = get_beatmapid[0]
		o_url = osu_api + "get_beatmaps?k=" + osu_key + "&b=" + str(r_selected)
		log("> > Getting details for beatmap '"+str(r_selected)+"'...")
		async with aiohttp.ClientSession() as cs:
			async with cs.get(o_url) as g:
				ges = await g.json()
				if ges:
					r_mods = np.random.randint(0,10)
					if r_mods == 0:
						mod = "HD"
					if r_mods == 1:
						mod = "HR"
					if r_mods == 2:
						mod = "SD"
					if r_mods ==3:
						mod = "DT"
						if float(ges[0]["diff_approach"]) > 9 or float(ges[0]["difficultyrating"]) > 5:
							mod = ""
					if r_mods == 4: 
						mod = "FL"
						if float(ges[0]["difficultyrating"]) > 4.5:
							mod = ""
					if r_mods == 5:
						mod = "EZ"
					if r_mods == 6:
						mod = "HT"
					if r_mods >= 7:
						mod = ""
					log("> > Challenge Mods: " + mod)
					r_win_condition = np.random.randint(0,4)
					if r_win_condition == 0:
						win = "Score"
						log("> > Challenge Win Condition: " + win)
						o_url = osu_api + "get_scores?k=" + osu_key + "&b=" + str(ges[0]["beatmap_id"])
						log("> > > Getting Scores...")
						async with aiohttp.ClientSession() as cs:
							async with cs.get(o_url) as g:
								tes = await g.json()
								if tes:
									high_score = int(tes[0]["score"])
									low_score = int(tes[len(tes)-1]["score"])
									get_perc = np.random.randint(75,90)/100
									getpass = int(int((high_score + low_score) / 2) * get_perc) 
									lastplay_modif = tes[0]["enabled_mods"]
									if lastplay_modif != "" or lastplay_modif != "0" or lastplay_modif !=0:
										used_mods = GetMods(lastplay_modif)
									log("> > > Configuring Score.")
									if used_mods:
										gm = ""
										for mods in used_mods:
											gm = gm + osu_mods_t[str(mods)] + ""
									else:
										gm = ""
									if "HR" in gm:
										getpass = int(getpass - (getpass * 0.06))
									if "HD" in gm:
										getpass = int(getpass - (getpass * 0.06))
									if "DT" in gm:
										getpass = int(getpass - (getpass * 0.12))
									if "FL" in gm: 
										getpass = int(getpass - (getpass * 0.12))
									if mod == "EZ":
										getpass = int(getpass / 2)
									if mod == "HT":
										getpass = int(getpass / 3)
									getpass = int(getpass/1000)*1000
									if getpass < 0:
										getpass = 0
								else:
									getpass = 0
					if r_win_condition ==1:
						win = "Accuracy"
						log("> > Challenge Win Condition: " + win)
						getpass = np.random.randint(90,99)
					if r_win_condition == 2:
						win = "Combo"
						log("> > Challenge Win Condition: " + win)
						min_combo = int(ges[0]["max_combo"])-100
						if min_combo < 0:
							min_combo = 0
						getpass = np.random.randint(min_combo,int(ges[0]["max_combo"]))
					if r_win_condition == 3:
						win = "Low Accuracy"
						log("> > Challenge Win Condition: " + win)
						getpass = np.random.randint(80,90)
					log("> > Challenge Pass Condition: " + str(getpass))
					log("> > Inserting into database...")
					BM_ID = ges[0]["beatmap_id"]
					BM_ARTIST = ges[0]["artist"]
					BM_TITLE = ges[0]["title"]
					BM_VERSION = ges[0]["version"]
					BM_SETID = ges[0]["beatmapset_id"]
					BM_CREATOR = ges[0]["creator"]
					TIME_ADDED = str(int(time.time()))
					mysql_quer = "INSERT INTO challenge (BEATMAP_ID,MODS,WIN_CONDITION,PASS_CONDITION,BM_ARTIST,BM_TITLE,BM_VERSION,BM_CREATOR,ADDED,BM_SETID) VALUES ("+str(ges[0]["beatmap_id"])+",'"+mod+"','"+win+"',"+str(getpass)+",'"+BM_ARTIST.replace("'","\\'")+"','"+BM_TITLE.replace("'","\\'")+"','"+BM_VERSION.replace("'","\\'")+"','"+BM_CREATOR.replace("'","\\'")+"',"+TIME_ADDED+","+str(BM_SETID)+")"
					await mysql_curs.execute(mysql_quer)
					await mysql_conn.commit()
					log("> > Selecting from database...")
					mysql_quer = "SELECT DIWOR FROM challenge WHERE ADDED = '"+TIME_ADDED+"' and BM_TITLE = '"+BM_TITLE.replace("'","\\'")+"'"
					await mysql_curs.execute(mysql_quer)
					t_result = await mysql_curs.fetchone()
					log("> Challenge has been added to database!")
					text = ""
					text = text + "["+str(t_result[0])+"] - **New " + win + " Challenge!**\r\n"
					if mod=="":
						do_mod = "any mods (including no mod, NF not included.)"
					else:
						do_mod = "the " + mod + " mod and any others you want (NF not included)."
					text = text + "Pass [" + BM_ARTIST + " - " + BM_TITLE + " ["+BM_VERSION+"] (by "+BM_CREATOR+")](http://osu.ppy.sh/b/"+BM_ID+") [[DD]](http://themeq.xyz/r.php?b="+BM_SETID+") [[BC]](http://bloodcat.com/osu/?q="+BM_ID+") with "
					if win == "Low Accuracy":
						text = text + "less than {0:,}".format(int(getpass))
					else:
						text = text + "at least {0:,}".format(int(getpass))
					if win == "Accuracy" or win == "Low Accuracy":
						text=text + "%"
					text=text + " " + win + " and using "+do_mod + "\r\n\r\n"
				else: 
					text = "Couldn't get beatmap details :("
	mysql_conn.close()
	log("--------------------------------")
	log("-- New Challenge Created      --")
	log("--------------------------------")
	return text

@bot.command(pass_context=True)
@commands.has_permissions(manage_channels=True)
async def newchallenge(ctx):
	'''Used to set a new challenge.'''
	await bot.delete_message(ctx.message)
	sender_author_id = ctx.message.author.id
	sender_author_name = ctx.message.author.name
	mysql_conn = await aiomysql.connect(host= mysql_host, port= 3306, user= mysql_user, password= mysql_pass, db= mysql_data)
	mysql_curs = await mysql_conn.cursor()
	mysql_quer = "SELECT PLAYER_NAME FROM linked_players WHERE DISCORD_ID = '" + str(sender_author_id) + "' AND LINKED = 1"
	await mysql_curs.execute(mysql_quer)
	this_player = await mysql_curs.fetchone()
	log("--------------------------------")
	log("-- New Challenge requested by "+str(this_player[0])+" --")
	log("--------------------------------")
	if ctx.message.channel.id == bot_channel:
		text = await getchallenge()
		embed = discord.Embed(colour=discord.Colour(0xFFFF00), description=text)
		await bot.send_message(ctx.message.channel,embed=embed)
	else: 
		await bot.send_message(ctx.message.channel,embed=olembed(0xFF0000,":no_entry: | "+this_player[0]+" - You can't use that command here!"))
	mysql_conn.close()

@bot.command(pass_context=True)
async def challenges(ctx):
	'''Used to check the list of challenges.'''
	await bot.delete_message(ctx.message)
	sender_author_id = ctx.message.author.id
	sender_author_name = ctx.message.author.name
	mysql_conn = await aiomysql.connect(host= mysql_host, port= 3306, user= mysql_user, password= mysql_pass, db= mysql_data)
	mysql_curs = await mysql_conn.cursor()
	mysql_quer = "SELECT PLAYER_NAME FROM linked_players WHERE DISCORD_ID = '" + str(sender_author_id) + "' AND LINKED = 1"
	await mysql_curs.execute(mysql_quer)
	this_player = await mysql_curs.fetchone()
	log("--------------------------------")
	log("-- Challenges requested by "+str(this_player[0])+" --")
	log("--------------------------------")
	if ctx.message.channel.id == bot_channel:
		mysql_conn = await aiomysql.connect(host= mysql_host, port= 3306, user= mysql_user, password= mysql_pass, db= mysql_data)
		mysql_curs = await mysql_conn.cursor()
		mysql_quer = "SELECT * FROM challenge WHERE winner=0 ORDER BY DIWOR ASC LIMIT 0,5"
		await mysql_curs.execute(mysql_quer)
		result = await mysql_curs.fetchall()
		text = "**Current Active Challenges**\r\n\r\n"
		text = text + "Challenges will not complete if you use **NF**.\r\n\r\n"
		for row in result:
			tr = int(row[10]+21600)-int(time.time())
			m, s = divmod(tr, 60)
			h, m = divmod(m, 60)
			rt = "%d:%02d:%02d" % (h, m, s)
			mi = int(tr / 60)
			if tr < 60:
				rt = "Under a Minute!"
			text = text + "[" + str(row[0]) + "] - **" + row[3] + " Challenge!** [Expires in "+ str(rt)+" | Bounty of "+str(getBounty(mi))+" points]\r\n"
			if row[2]=="":
				do_mod = "any mods."
			else:
				do_mod = "any mods with the " + row[2] + " mod."
			text = text + "Pass [" + row[5] + " - " + row[6] + " ["+row[7]+"] (by "+row[8]+")](http://osu.ppy.sh/b/"+str(row[1])+") [[DD]](http://themeq.xyz/r.php?b="+str(row[11])+") [[BC]](http://bloodcat.com/osu/?q="+str(row[1])+") with "
			if row[3] == "Low Accuracy":
				text = text + "less than {0:,}".format(int(row[4]))
			else:
				text = text + "at least {0:,}".format(int(row[4]))
			if row[3] == "Accuracy" or row[3] == "Low Accuracy":
				text=text + "%"
			text=text + " " + row[3] + " and using "+do_mod + "\r\n\r\n"
		embed = discord.Embed(colour=discord.Colour(0xFFFF00), description=text)
		await bot.send_message(ctx.message.channel,embed=embed)
		mysql_quer = "SELECT * FROM challenge WHERE winner=0 ORDER BY DIWOR ASC LIMIT 5,10"
		await mysql_curs.execute(mysql_quer)
		result = await mysql_curs.fetchall()
		text = ""
		for row in result:
			tr = int(row[10]+21600)-int(time.time())
			m, s = divmod(tr, 60)
			h, m = divmod(m, 60)
			rt = "%d:%02d:%02d" % (h, m, s)
			mi = int(tr / 60)
			if tr < 60:
				rt = "Under a Minute!"
			
			text = text + "[" + str(row[0]) + "] - **" + row[3] + " Challenge!** [Expires in "+ str(rt)+" | Bounty of "+str(getBounty(mi))+" points]\r\n"
			if row[2]=="":
				do_mod = "any mods."
			else:
				do_mod = "any mods with the " + row[2] + " mod."
			text = text + "Pass [" + row[5] + " - " + row[6] + " ["+row[7]+"] (by "+row[8]+")](http://osu.ppy.sh/b/"+str(row[1])+") [[DD]](http://themeq.xyz/r.php?b="+str(row[11])+") [[BC]](http://bloodcat.com/osu/?q="+str(row[1])+") with "
			if row[3] == "Low Accuracy":
				text = text + "less than {0:,}".format(int(row[4]))
			else:
				text = text + "at least {0:,}".format(int(row[4]))
			if row[3] == "Accuracy" or row[3] == "Low Accuracy":
				text=text + "%"
			text=text + " " + row[3] + " and using "+do_mod + "\r\n\r\n"
		embed = discord.Embed(colour=discord.Colour(0xFFFF00), description=text)
		await bot.send_message(ctx.message.channel,embed=embed)
	else:
		await bot.send_message(ctx.message.channel,embed=olembed(0xFF0000,"You can't use that command here!"))
	mysql_conn.close()

@bot.command(pass_context=True,aliases=['c'])
async def complete(ctx,id : int=0):
	'''Used to submit your challenge!'''
	await bot.delete_message(ctx.message)
	sender_author_id = ctx.message.author.id
	sender_author_name = ctx.message.author.name
	mysql_conn = await aiomysql.connect(host= mysql_host, port= 3306, user= mysql_user, password= mysql_pass, db= mysql_data)
	mysql_curs = await mysql_conn.cursor()
	mysql_quer = "SELECT PLAYER_NAME FROM linked_players WHERE DISCORD_ID = '" + str(sender_author_id) + "' AND LINKED = 1"
	await mysql_curs.execute(mysql_quer)
	this_player = await mysql_curs.fetchone()
	log("--------------------------------")
	log("-- Complete Requested by "+str(this_player[0]))
	log("--------------------------------")
	if ctx.message.channel.id == bot_channel:
		msg = await bot.send_message(ctx.message.channel,embed=olembed(0xFFFF00,":zap: | " + this_player[0] + " - Checking..."))
		if id==0:
			await bot.edit_message(msg,embed=olembed(0xFF0000,":no_entry: | " + this_player[0] + " - You didn't specify a challenge ID."))
		else:
			mysql_quer = "SELECT * FROM challenge WHERE DIWOR = " + str(id) + " AND WINNER = 0"
			await mysql_curs.execute(mysql_quer)
			result = await mysql_curs.fetchone()
			if result:
				mysql_quer = "SELECT * FROM linked_players WHERE DISCORD_ID = '" + str(sender_author_id) + "' AND LINKED = 1"
				await mysql_curs.execute(mysql_quer)
				p_result = await mysql_curs.fetchone()
				if p_result:
					if int(time.time()) - 300 > p_result[21]:
						player_id = p_result[2]
						o_url = osu_api + "get_user_recent?k=" + osu_key + "&u=" + str(player_id) + "&m=0&limit=1"
						log("Getting scores for this user...")
						async with aiohttp.ClientSession() as cs:
							async with cs.get(o_url) as a:
								sco = await a.json()
								if sco:
									lastplay_modif = sco[0]['enabled_mods']
									lastplay_beatmap = sco[0]['beatmap_id']
									lastplay_score = int(sco[0]['score'])
									lastplay_maxco = sco[0]['maxcombo']
									lastplay_fifty = sco[0]['count50']
									lastplay_hundr = sco[0]['count100']
									lastplay_three = sco[0]['count300']
									lastplay_misse = sco[0]['countmiss']
									lastplay_accur = ((((int(lastplay_three) * 300) + (int(lastplay_hundr) * 100) + (int(lastplay_fifty) * 50) + (int(lastplay_misse) * 0)) / ((int(lastplay_three) + int(lastplay_hundr) + int(lastplay_fifty) + int(lastplay_misse)) * 300)) * 100)
									log(str(lastplay_beatmap) + "=" + str(result[1]))
									if str(lastplay_beatmap) == str(result[1]):
										challenge_complete = 0
										if result[3]=="Accuracy":
											log(str(float(lastplay_accur)) + " > " + str(float(result[4])))
											if float(lastplay_accur) >= float(result[4]):
												challenge_complete = 1
										elif result[3]=="Combo":
											log(str(int(lastplay_maxco)) + " > " + str(int(result[4])))
											if int(lastplay_maxco) >= int(result[4]):
												challenge_complete = 1
										elif result[3]=="Score":
											log(str(int(lastplay_score)) + " > " + str(int(result[4])))
											if int(lastplay_score) >= int(result[4]):
												challenge_complete = 1
										elif result[3]=="Low Accuracy":
											log(str(int(lastplay_accur)) + " < " + str(int(result[4])))
											if int(lastplay_accur) <= int(result[4]):
												challenge_complete = 1
										if challenge_complete == 1:
											log("MODS: " + str(result[2]))
											
											if result[2] != "":
												if lastplay_modif != "" or lastplay_modif != "0" or lastplay_modif !=0:
													used_mods = GetMods(lastplay_modif)
												if used_mods:
													gm = ""
													for mods in used_mods:
														gm = gm + osu_mods_t[str(mods)] + ""
												else:
													gm = ""
												log("COMPARE MODS: "+  gm +"="+ result[2])
												if result[2] in gm:
													challenge_complete = 1
												else:
													challenge_complete = 0
												if "NF" in gm:
													challenge_complete = 0
										if challenge_complete == 1:
											tr = int(result[10]+21600)-int(time.time())
											mi = int(tr/60)
											ro = getBounty(mi)
											bo = 0
											r = np.random.randint(0,100)
											log("BONUS IF LESS THEN 6: "+str(r))
											if r <= 5:
												bo=ro*9
												if bo>500:
													bo=500
												text = ":open_mouth: | Wew! " + p_result[3] + " just completed challenge "+str(id)+" and claimed a bounty of "+str(int(ro))+" points!\r\n\r\n"
												text = text + ":moneybag: | OMG! "+p_result[3]+" just gained "+str(int(bo))+" bonus points!\r\n\r\n"
											else:
												text = ":open_mouth: | Wew! " + p_result[3] + " just completed challenge "+str(id)+" and claimed a bounty of "+str(int(ro))+" points!\r\n\r\n"
											mysql_quer = "UPDATE linked_players SET SCORE_CHALLENGE = SCORE_CHALLENGE + "+str(int(ro+bo))+", CHALLENGE_COOLDOWN = "+str(int(time.time()))+" WHERE PLAYER_ID = '" + str(player_id) + "'"
											await mysql_curs.execute(mysql_quer)
											await mysql_conn.commit()
											mysql_quer = "UPDATE challenge SET WINNER = " + str(player_id) + " WHERE DIWOR = " + str(id)
											await mysql_curs.execute(mysql_quer)
											await mysql_conn.commit()
											text = text + await getchallenge()
											embed = discord.Embed(colour=discord.Colour(0x00AA00), description=text)
											await bot.edit_message(msg,embed=embed)
										else:
											await bot.edit_message(msg,embed=olembed(0xFF0000,":sob: | Sorry " + this_player[0] + ", You didn't pass the requirements to beat challenge "+str(id)+"."))
									else:
										await bot.edit_message(msg,embed=olembed(0xFF0000,":no_entry: | " + this_player[0] + " - Your latest play does not match up with the beatmap for challenge "+str(id)+"."))
								else:
									await bot.edit_message(msg,embed=olembed(0xFF0000,":no_entry: | " + this_player[0] + " - Couldn't find your latest scores."))
					else:
						remaining = int(int(time.time()-300) - p_result[21])
						await bot.edit_message(msg,embed=olembed(0xFF0000,":timer: | " + this_player[0] + " - You are currently on a cooldown. You have to wait "+str(abs(remaining))+" seconds."))
				else:
					await bot.edit_message(msg,embed=olembed(0xFF0000,":no_entry: | " + this_player[0] + " - Your account is not linked. Please speak to @Staff."))
			else:
				await bot.edit_message(msg,embed=olembed(0xFF0000,":no_entry: | " + this_player[0] + " - Couldn't find a challenge with the ID '"+str(id)+"'. It may have already been done."))
	else:
		await bot.edit_message(msg,embed=olembed(0xFF0000,"You can't use that command here!"))
	mysql_conn.close()

@bot.command(pass_context=True)
async def scoreboard(ctx):
	'''Used to get the challenge scoreboard.''' 
	await bot.delete_message(ctx.message)
	sender_author_id = ctx.message.author.id
	sender_author_name = ctx.message.author.name
	mysql_conn = await aiomysql.connect(host= mysql_host, port= 3306, user= mysql_user, password= mysql_pass, db= mysql_data)
	mysql_curs = await mysql_conn.cursor()
	mysql_quer = "SELECT PLAYER_NAME FROM linked_players WHERE DISCORD_ID = '" + str(sender_author_id) + "' AND LINKED = 1"
	await mysql_curs.execute(mysql_quer)
	this_player = await mysql_curs.fetchone()
	mysql_conn.close()
	log("--------------------------------")
	log("-- Scoreboard Requested by "+str(this_player[0]))
	log("--------------------------------")
	if ctx.message.channel.id == bot_channel:
		mysql_conn = await aiomysql.connect(host= mysql_host, port= 3306, user= mysql_user, password= mysql_pass, db= mysql_data)
		mysql_curs = await mysql_conn.cursor()
		mysql_quer = "SELECT * FROM linked_players WHERE linked=1 and SCORE_CHALLENGE > 0 ORDER BY SCORE_CHALLENGE DESC LIMIT 0,50"
		await mysql_curs.execute(mysql_quer)
		result = await mysql_curs.fetchall()
		text = "**Challenge Scoreboard**\r\n\r\n"
		count = 1
		for row in result:
			if count >= 1 and count <=3:
				if count==1:
					text=text + ":first_place: "
				if count==2:
					text=text + ":second_place: "
				if count==3:
					text=text + ":third_place: "
				text = text + "**{0} - {1} with {2} points.**\r\n".format(Ordinal(count),row[3],str(row[20]))
			else:
				text = text + "{0} - {1} with {2} points.\r\n".format(Ordinal(count),row[3],str(row[20]))
			count=count + 1
		embed = discord.Embed(colour=discord.Colour(0x0000FF), description=text)
		await bot.send_message(ctx.message.channel,embed=embed)
		mysql_conn.close()
	else:
		await bot.send_message(ctx.message.channel,embed=olembed(0xFF0000,":no_entry: | You can't use that command here!"))

async def my_background_task():
	channel = discord.Object(id=bot_channel)
	while not bot.is_closed:
		log("--------------------------------")
		log("-- Running Background Task... --")
		log("--------------------------------")
		mysql_conn = await aiomysql.connect(host= mysql_host, port= 3306, user= mysql_user, password= mysql_pass, db= mysql_data)
		mysql_curs = await mysql_conn.cursor()
		mysql_quer = "SELECT * FROM challenge WHERE WINNER < 1 ORDER BY DIWOR DESC LIMIT 0,10"
		await mysql_curs.execute(mysql_quer)
		result = await mysql_curs.fetchall()
		log("> Current time is: "+str(int(time.time())))
		for row in result:
			log("Checking Challenge ID: "+str(row[0]))
			log("> Beatmap time is: "+str(int((row[10]) + 21600)))
			if int(time.time()) > int(int(row[10]) + 21600):
				log("> > Current Time is greater than Beatmap Time.")
				log("> > Expiring Challenge ID: "+str(row[0]))
				mysql_quer = "UPDATE challenge SET WINNER=1 WHERE DIWOR = "+str(row[0])
				await mysql_curs.execute(mysql_quer)
				await mysql_conn.commit()
				text = ":skull_crossbones: | Challenge ["+str(row[0])+"] expired.\r\n\r\n"
				text = text + await getchallenge()
				embed = discord.Embed(colour=discord.Colour(0xFF0000), description=text)
				await bot.send_message(channel,embed=embed)
			elif int(time.time()) > int(int(row[10]) + 20400) and int(time.time()) < int(int(row[10]) + 20455):
				log("> > Current Time is nearly greater than Beatmap Time.")
				log("> > Sending Alert about expiring Challenge ID: "+str(row[0]))
				text = ":sweat: | Challenge ["+str(row[0])+"] is expiring in 20 minutes!\r\n\r\n"
				embed = discord.Embed(colour=discord.Colour(0xFF0000), description=text)
				await bot.send_message(channel,embed=embed)
			else:
				log("> > Current Time is less than Beatmap Time by "+str((int(time.time()) - int(int(row[10]))))+"s..")
		mysql_conn.close()
		log("--------------------------------")
		log("-- Background Task Finished ----")
		log("--------------------------------")
		await asyncio.sleep(60)

@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def restartbot(ctx):
	'''Restart the bot!'''
	await bot.delete_message(ctx.message)
	exit()

bot.loop.create_task(my_background_task())
bot.run(dis_key)