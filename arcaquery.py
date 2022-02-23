import sys
import arcadb
from datetime import datetime
import xlsxwriter

def cleanCountryName(name):
    return name.replace(" ", "_").replace("(", "_").replace(")", "")

def timestamp():
    return int(datetime.utcnow().timestamp())

class Results(object):
    countryid = 0
    country = ""
    virus_ids = []
    viruses = []
    rawdata = []
    data = []
    headers = []
    colnames = []
    csvfile = ""
    tsvfile = ""
    xlsfile = ""
    
    def __init__(self, countryid):
        self.countryid = countryid
        self.virus_ids = []
        self.viruses = []
        self.rawdata = []
        self.data = []
        self.headers = []
        
    def query(self, db, virus_ids, start_year, start_week, end_year, end_week):
        self.country = arcadb.getCountryName(db, self.countryid)
        clean = cleanCountryName(self.country)
        ts = timestamp()
        self.csvfile = "{}_{}.csv".format(clean, ts)
        self.tsvfile = "{}_{}.tsv".format(clean, ts)
        self.xlsfile = "{}_{}.xlsx".format(clean, ts)

        self.virus_ids = virus_ids
        self.viruses = arcadb.getVirusNames(db, virus_ids)
        self.rawdata = arcadb.getCases(db, self.countryid, virus_ids, start_year, start_week, end_year, end_week)

        self.headers = "<TR class='w3-green'><TH>Year</TH><TH class='w3-right-align'>Week</TH>"
        self.colnames = ["Country", "Year", "Week"]
        self.rowformat = "<TR><TD>{}</TD><TD class='w3-right-align'>{}</TD>"
        for v in self.viruses:
            self.headers += "<TH class='w3-right-align'>" + v + "</TH>"
            self.colnames.append(v)
            self.rowformat += "<TD class='w3-right-align'>{:,d}</TD>"
        self.headers += "</TR>\n"
        self.rowformat += "</TR>\n"

        ncolumns = len(self.viruses)
        row = ["", ""] + [0]*ncolumns
        vp = {}
        pos = 2
        for v in self.virus_ids:
            vp[int(v)] = pos
            pos += 1
                
        for rd in self.rawdata:
            #sys.stdout.write("{}<BR>".format(rd))
            if rd[0] == start_year and rd[1] < start_week:
                continue
            if rd[0] == end_year and rd[1] > end_week:
                continue
            if rd[0] != row[0] or rd[1] != row[1]:
                if row[0]:
                    self.data.append(row)
                    row = ["", ""] + [0]*ncolumns
                row[0] = rd[0]
                row[1] = rd[1]
                
            virus = rd[2]
            field = vp[virus]
            #sys.stdout.write("{}\n".format(field))
            row[field] = rd[3]
        self.data.append(row)
        
    def generate_plot(self, divname):
        nviruses = len(self.virus_ids)
        ntrace = 1
        traces = []
        sys.stdout.write("""function draw_{}() {{""".format(divname))
        for i in range(nviruses):
            j = i + 2
            virus_name = self.viruses[i]
            tracename = "trace" + str(ntrace)
            traces.append(tracename)

            xs = []
            ys = []
            for row in self.data:
                xs.append("{:.2f}".format(row[0] + row[1] / 52))
                ys.append(row[j])
                          
            sys.stdout.write("""
 var {} = {{
  x: [{}],
  y: [{}],
  type: 'bar',
  name: '{}',
}};

""".format(tracename, ",".join(xs), ",".join([ str(y) for y in ys ]), virus_name))
            ntrace += 1
        sys.stdout.write("""
var data = [{}];

var layout = {{
  title: '{}',
  xaxis: {{
    tickangle: -90
  }},
  barmode: 'group'
}};

Plotly.newPlot('{}', data, layout);
}}
""".format(", ".join(traces), self.country, divname))


    def write_to_file(self, filename, delimiter=','):
        with open(filename, "w") as out:
            out.write(delimiter.join(self.colnames) + "\n")
            for row in self.data:
                out.write(self.country + delimiter + delimiter.join([str(x) for x in row]) + "\n")
                
    def write_to_excel(self, filename):
        wb = xlsxwriter.Workbook(filename, {'strings_to_numbers': True})
        ### workbook.set_properties({'author': 'A. Riva, ariva@ufl.edu', 'company': 'DiBiG - ICBR Bioinformatics'}) # these should be read from conf or command-line
        bold = wb.add_format({'bold': 1})
        ws = wb.add_worksheet("Cases")
        row = 0
        col = 0
        for cn in self.colnames:
            ws.write(row, col, self.colnames[col], bold)
            col += 1

        r = 1
        for row in self.data:
            ws.write(r, 0, self.country)
            col = 1
            for x in row:
                ws.write(r, col, x)
                col += 1
            r += 1
        wb.close()
        
