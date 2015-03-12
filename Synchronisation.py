#! /usr/bin/python2.7
# -*-  coding: utf-8 -*-
__author__ = 'ovnislash'

import urllib, urllib2, json, jsonpickle, sqlite3, datetime, time, uuid

class Synchronisation(object):
    def __init__(self):
        self.connexion = sqlite3.connect('DB.sqlite3')
        self.curseur = self.connexion.cursor()
        self.API_ADRESS = "http://192.168.43.219:5000/"
        self.DELAY =  900

        # Initialisation de la BDD
        bdd = open('DB.sqlite3', 'r')
        if bdd.read() == "" :
            self.installBDD()

        self.routine()

        self.connexion.close()

    def installBDD(self):
        self.curseur.execute('CREATE TABLE IF NOT EXISTS scheduling(id integer, date_start datetime, date_end datetime, promotion_id varchar, professor_id varchar, updated timestamp)')
        self.curseur.execute('CREATE TABLE IF NOT EXISTS user(id varchar, promotion_id varchar null)')
        self.curseur.execute('CREATE TABLE IF NOT EXISTS presence(user_id varchar, date datetime, uploaded integer default 0)')
        self.connexion.commit()

    def sendRequest(self,url,updated = False):
        try :
            request = urllib2.Request(url)
            if updated :
                self.curseur.execute('SELECT MAX(updated) FROM scheduling')
                last_scheduling_updated = self.curseur.fetchone()
                lsu = float(0)
                if last_scheduling_updated != None and last_scheduling_updated[0] != None :
                    lsu = last_scheduling_updated[0]
                request.add_header('If-Modified-Since', datetime.datetime.fromtimestamp(lsu).strftime("%d %b %Y %H:%M:%S GMT"))
            response = urllib2.urlopen(request)
            return json.load(response)
        except urllib2.HTTPError as e:
            if e.getcode() == 404 :
                print "ALREADY UP TO DATE"
            else :
                print "ERREUR "+str(e.getcode())
            return None
        except urllib2.URLError as e:
			print "CONNECTION SERVER IMPOSSIBLE"

    def requestSchedulings(self) :

        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0,8*6,8)][::-1])

        url = self.API_ADRESS+"schedulings?raspberry_id="+mac
        schedulings = self.sendRequest(url,True)

        print schedulings
        return schedulings

    def requestUsers(self) :
        # Récupération des promo_ids
        promotion_ids = []
        professor_ids = []
        users1 = []
        users2 = []
        self.curseur.execute('SELECT promotion_id FROM scheduling GROUP BY promotion_id')
        all_promotion_id = self.curseur.fetchall()
        for promotion_id in all_promotion_id :
            promotion_ids.append(promotion_id[0])

        if(len(promotion_ids) > 0) :
            url = self.API_ADRESS+"users?promotion_id="+",".join(promotion_ids)
            users1 = self.sendRequest(url)

        self.curseur.execute('SELECT professor_id FROM scheduling GROUP BY professor_id')
        all_professor_id = self.curseur.fetchall()
        for professor_id in all_professor_id :
            professor_ids.append(professor_id[0])

        if(len(professor_ids) > 0) :
            url = self.API_ADRESS+"users?id="+",".join(professor_ids)
            users2 = self.sendRequest(url)

        print users1 + users2
        return users1 + users2

    def findAllSchedulingsId(self) :
        check_schedulings_id = []
        self.curseur.execute('SELECT id FROM scheduling')
        rs_scheduling_ids = self.curseur.fetchall()
        for scheduling_id in rs_scheduling_ids :
            check_schedulings_id.append(scheduling_id[0])
        return  check_schedulings_id

    def findAllUsersId(self) :
        check_users_id = []
        self.curseur.execute('SELECT id FROM user')
        rs_user_ids = self.curseur.fetchall()
        for user_id in rs_user_ids :
            check_users_id.append(user_id[0])
        return check_users_id

    def sentPresence(self) :
        # Envoie des présences sur l'URI : /presences
        self.curseur.execute('SELECT * FROM presence WHERE uploaded = 0')
        presences = self.curseur.fetchall()

        presences_array = []

        for presence in presences :
            tmp = {}
            tmp['user_id'] = presence[0]
            tmp['date'] = presence[1]
            presences_array.append(tmp)

        if len(presences_array) != 0 :
            presences_json = jsonpickle.encode(presences_array)
            print presences_json

            try:
                url = self.API_ADRESS+"presences/"
                request = urllib2.Request(url,presences_json,{"content-type" : "application/json"})
                response = urllib2.urlopen(request)
                self.curseur.execute('UPDATE presence SET uploaded = 1 WHERE uploaded = 0')
                self.connexion.commit()
                print response.read()
                print "Sent presence...OK"

            except urllib2.HTTPError as e:
                print "ERREUR..."+str(e.getcode())
                print "Sent presence...FAILED"
                pass

    def checkUser(self, id) :
        self.connexion = sqlite3.connect('DB.sqlite3')
        self.curseur = self.connexion.cursor()
        print "User authentification's starting..."

        now = time.time()

        # On vérifie le planning du créneau horraire et si l'utilisateur est dans cette promotion (tenter un join)
        self.curseur.execute("SELECT s.date_start, s.date_end FROM scheduling AS s INNER JOIN user AS u ON u.id = '"+id+"' AND ( u.promotion_id = s.promotion_id OR u.id = s.professor_id ) WHERE s.date_start < "+str(now)+" AND s.date_end > "+str(now))
        scheduling = self.curseur.fetchone()

        if (scheduling != None) :
            print "User found..."
            # On recherche si l'utilisateur a déjà enregistré sa présence
            self.curseur.execute("SELECT user_id FROM presence WHERE user_id='"+id+"' AND date BETWEEN '"+str(scheduling[0])+"' AND '"+str(scheduling[1])+"'")
            presence = self.curseur.fetchone()

            if (presence != None):
                print "User already recorded..."
                return 2
            else :
                self.curseur.execute("INSERT INTO presence (user_id, date) VALUES ('"+id+"', "+str(now)+")")
                self.connexion.commit()
                self.connexion.close()
                print "User's authentification...OK"
                return 1

        print "User's authentification...FAILED"
        self.connexion.close()
        return 0

    def cleanBDD(self):
        now = str(time.time())
        nowless1day = str(time.time()-86400)

        # Suppressions des présences uploadés et qui ne sont plus dans les créneaux horraires des schedulings
        self.curseur.execute("DELETE FROM presence WHERE uploaded = 1 AND date < "+nowless1day)

        # Suppressions des schedulings dépassés
        self.curseur.execute("DELETE FROM scheduling WHERE date_end < "+nowless1day)

        # Suppressions des utilisateurs qui ne sont plus dans les créneaux horraires
        #self.curseur("DELETE FROM user AS u INNER JOIN scheduling AS s ON u.promotion_id <> s.promotion.id AND u.id <> s.professor_id")
        self.curseur.execute("DELETE FROM user WHERE promotion_id NOT IN (SELECT promotion_id FROM scheduling WHERE date_end > "+now+") OR id IN (SELECT professor_id FROM scheduling WHERE date_end > "+now+")")

        print "Clean Database...OK"

    def routine(self):
        i = j = 0
        new_schedulings = []
        new_users = []
        self.connexion = sqlite3.connect('DB.sqlite3')
        self.curseur = self.connexion.cursor()
        print "Synchronisation's routine...STARTING"

        # Demande des derniers plannings sur l'URI : /schedulings?room={mac_adress}&updated={last_updated}
        schedulings = self.requestSchedulings()

        if schedulings != None :
            # Récupération des plannings existants
            check_schedulings_id = self.findAllSchedulingsId()

            # Enregistrement et maj des plannings
            for scheduling in schedulings:
                if scheduling['id'] in check_schedulings_id :
                    i += 1
                    self.curseur.execute ("UPDATE scheduling SET date_start = "+str(scheduling['date_start']-self.DELAY)+", date_end = "+str(scheduling['date_end'])+", promotion_id = '"+scheduling['promotion_id']+"', professor_id = '"+scheduling['user_id']+"', updated = "+str(scheduling['updated'])+" WHERE id = "+str(scheduling['id']))
                else :
                    i += 1
                    new_schedulings.append("("+str(scheduling['id'])+","+str(scheduling['date_start']-self.DELAY)+","+str(scheduling['date_end'])+",'"+scheduling['promotion_id']+"','"+scheduling['user_id']+"',"+str(scheduling['updated'])+")")

            if len(new_schedulings) > 0 :
                self.curseur.execute("INSERT INTO scheduling ('id','date_start','date_end','promotion_id','professor_id','updated') VALUES "+", ".join(new_schedulings))
            print "Requesting schedulings...OK"

            # S'il y a du neuf dans les plannings, on récupère une liste des utilisateurs sur l'URI : /users?proffesor_ids={ids}&promo_ids={ids}
            if i > 0 :
                self.connexion.commit()

                # Récupération des utilisateurs existants
                check_users_id = self.findAllUsersId()

                # Demande les utilisateurs concernés par les plannings
                users = self.requestUsers()

                if users != None :
                    # Enregistrement et maj des utilisateurs
                    for user in users:
                        if user['id'] in check_users_id :
                            j += 1
                            self.curseur.execute ("UPDATE user SET promotion_id = '"+('null', user['promotion_id'])[user['promotion_id'] != None]+"' WHERE id = '"+user['id']+"'")
                        else :
                            j += 1
                            new_users.append("('"+user['id']+"','"+('null', user['promotion_id'])[user['promotion_id'] != None]+"')")
                    if len(new_users) > 0 :
                        self.curseur.execute("INSERT INTO user ('id','promotion_id') VALUES "+", ".join(new_users))
                    if j > 0 :
                        self.connexion.commit()
                    print "Requesting users...OK"

        # Envoi des présences
        self.sentPresence()

        # Suppression des données dépassés
        self.cleanBDD()

        self.connexion.close()
        print "Synchronisation's routine...DONE"

