FROM neo4j:5.16.0

# Copy your plugin
COPY plugins/*.jar /var/lib/neo4j/plugins/

# Configure Neo4j for GDS
RUN echo "dbms.security.procedures.unrestricted=gds.*" >> /var/lib/neo4j/conf/neo4j.conf && \
    echo "dbms.security.procedures.allowlist=gds.*" >> /var/lib/neo4j/conf/neo4j.conf && \
    echo "server.jvm.additional=-Dunsupported.dbms.udc.source=docker" >> /var/lib/neo4j/conf/neo4j.conf 